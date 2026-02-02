/*
 * Shelly Plus I4 (Gen3) – Remote Bridge Script (RPC-less / KVS-trigger)
 * Purpose: Let HA / RC8 trigger the SAME group actions as your autonomous i4
 *          script — without touching it and WITHOUT custom RPC handlers.
 *
 * How to trigger from HA:
 *   POST http://<I4-IP>/rpc/KVS.Set
 *     {"key":"ext_bridge_cmd","value":{"group":"A","token":"single_up"}}
 *   or
 *     {"key":"ext_bridge_cmd","value":{"group":"B","gesture":"double","dir":"down"}}
 *
 * The bridge polls KVS key "ext_bridge_cmd" at short intervals, executes
 * the request once, then clears the key to acknowledge.
 */

// ---------- Constants ----------
let KVS_A_TARGETS = "groupA_targets";
let KVS_B_TARGETS = "groupB_targets";
let KVS_DELAY     = "send_delay_ms";
let KVS_DEBUG     = "debug";
let KVS_KEY_CMD   = "coverex_cmd";       // destination key on targets
let KVS_MAILBOX   = "ext_bridge_cmd";    // mailbox key read by this bridge

// Optional: Basic Auth header for requests to target Shellys
let AUTH_HDR = null; // e.g. "Authorization: Basic dXNlcjpwYXNz"

// ---------- Runtime ----------
let SEND_DELAY_MS = 80;   // wird ggf. via KVS_DELAY überschrieben
let DEBUG = false;
let A_IPS = [];
let B_IPS = [];
let POLL_MS = 150;        // entspanntes Polling: 150–300 ms sind ok
let pollTimer = null;

// Anti-Überlauf / Watchdog
let mailboxBusy = false;

// ---------- Utils ----------
function isStr(x){ return typeof x === "string"; }
function isArr(x){
  return Array.isArray
    ? Array.isArray(x)
    : (x && typeof x.length === "number" && typeof x !== "string");
}
function toInt(x){ let n = parseInt(x,10); return isNaN(n) ? 0 : (n|0); }
function trim(s){
  s = String(s||"");
  let a=0,b=s.length;
  while(a<b && s.charCodeAt(a)<=32) a++;
  while(b>a && s.charCodeAt(b-1)<=32) b--;
  return s.slice(a,b);
}
function dequote(s){
  s=String(s||"");
  if(s.length>=2){
    let a=s.charCodeAt(0),b=s.charCodeAt(s.length-1);
    if((a===34&&b===34)||(a===39&&b===39)) return s.slice(1,-1);
  }
  return s;
}
function validIPv4(s){
  if(!isStr(s))return false;
  s=trim(s);
  let p=s.split('.');
  if(p.length!==4)return false;
  for(let i=0;i<4;i++){
    let q=p[i];
    if(q===""||q.length>3)return false;
    for(let j=0;j<q.length;j++){
      let c=q.charCodeAt(j);
      if(c<48||c>57) return false;
    }
    let n=parseInt(q,10);
    if(isNaN(n)||n<0||n>255)return false;
  }
  return true;
}

function parseTargetsDetailed(v){
  let raw=[]; let out={valid:[], invalid:[]};
  if(v===undefined||v===null) return out;
  if(isStr(v)){
    let s=trim(v);
    if(s.charAt(0)==='['){
      let parsed=null;
      try{parsed=JSON.parse(s);}catch(_e){parsed=null;}
      if(isArr(parsed)){
        for(let i=0;i<parsed.length;i++) raw.push(parsed[i]);
      } else {
        raw=s.split(',');
      }
    }
    else { raw=s.split(','); }
  } else if(isArr(v)){
    for(let i=0;i<v.length;i++) raw.push(v[i]);
  }
  else {
    raw=String(v).split(',');
  }

  for(let i=0;i<raw.length;i++){
    let s=dequote(trim(String(raw[i])));
    if(!s) continue;
    if(validIPv4(s)) out.valid.push(s); else out.invalid.push(s);
  }
  return out;
}

function httpGet(url, cb){
  let headers = {};
  if (AUTH_HDR){
    headers["Authorization"] =
      AUTH_HDR.indexOf(":")>0 ? ("Basic "+AUTH_HDR) : AUTH_HDR;
  }
  Shelly.call("HTTP.GET", { url:url, headers:headers, timeout:4 }, function(res){
    cb(res);
  });
}

// ---------- Loaders ----------
function loadDebug(cb){
  Shelly.call("KVS.Get", { key: KVS_DEBUG }, function(res, err){
    if(!err && res && res.value!==undefined && res.value!==null){
      let v=res.value;
      DEBUG=(v===true||v==="true"||v===1||v==="1");
    } else {
      DEBUG=false;
    }
    if (DEBUG) print("bridge DEBUG=", DEBUG);
    if (cb) cb();
  });
}

function loadDelay(cb){
  Shelly.call("KVS.Get", { key: KVS_DELAY }, function(res, err){
    if(!err && res && res.value!==undefined && res.value!==null){
      let n=toInt(res.value);
      if(n>=0&&n<=2000) SEND_DELAY_MS=n;
    }
    print("bridge send_delay_ms=", SEND_DELAY_MS);
    if (cb) cb();
  });
}

function logTargets(label, valid, invalid){
  print(label, "(valid)", JSON.stringify(valid));
  if(DEBUG && invalid && invalid.length)
    print(label, "(invalid,ignored)", JSON.stringify(invalid));
}

function loadGroup(key, assign, label, cb){
  Shelly.call("KVS.Get", { key:key }, function(res, err){
    let parsed={valid:[], invalid:[]};
    if(!err && res && res.value!==undefined && res.value!==null){
      parsed = parseTargetsDetailed(res.value);
    }
    assign(parsed.valid);
    logTargets(label+" targets", parsed.valid, parsed.invalid);
    if (cb) cb();
  });
}

function reloadAll(cb){
  loadDebug(function(){
    loadDelay(function(){
      loadGroup(KVS_A_TARGETS, function(v){A_IPS=v;}, "A", function(){
        loadGroup(KVS_B_TARGETS, function(v){B_IPS=v;}, "B", function(){
          if(cb) cb();
        });
      });
    });
  });
}

// ---------- Sender ----------
function sendTokenToList(token, list, label){
  if(!token) return { ok:false, err:"no_token" };
  let ips = list.slice(0);
  if(ips.length===0){
    if(DEBUG) print("bridge", label, "skip (no targets)", token);
    return { ok:false, err:"no_targets" };
  }
  let ok=0, fail=0;

  function step(i){
    if(i>=ips.length){
      print("bridge", label, "summary", token, "ok:",ok,"fail:",fail,"targets:",ips.length);
      return;
    }
    let ip=ips[i];
    let url="http://"+ip+"/rpc/KVS.Set?key="+KVS_KEY_CMD+"&value="+token;
    httpGet(url, function(res){
      if(res && res.code===200){
        if(DEBUG) print("bridge OK→", ip, token);
        ok++;
      } else {
        if(DEBUG) print("bridge ERR→", ip, token, "code:", res?res.code:"nores");
        fail++;
      }
      if(SEND_DELAY_MS>0)
        Timer.set(SEND_DELAY_MS, false, function(){ step(i+1); });
      else
        step(i+1);
    });
  }

  step(0);
  return { ok:true };
}

function tokenFromParams(p){
  if(!p) return null;
  if(isStr(p.token)) return p.token; // direct override
  let g=isStr(p.gesture)?p.gesture:null; // single|double|long
  let d=isStr(p.dir)?p.dir:null;         // up|down
  if(!g||!d) return null;
  if(g!=="single" && g!=="double" && g!=="long") return null;
  if(d!=="up" && d!=="down") return null;
  return g+"_"+d;
}

function pickGroupList(grp){
  if(!grp) return null;
  let G=String(grp).toUpperCase();
  if(G==="A") return { list:A_IPS, label:"A" };
  if(G==="B") return { list:B_IPS, label:"B" };
  return null;
}

// ---------- Mailbox polling (mit Busy-Flag & Heartbeat) ----------
function readMailboxOnce(cb){
  if (mailboxBusy){
    if (cb) cb(null);
    return;
  }
  mailboxBusy = true;

  Shelly.call("KVS.Get", { key: KVS_MAILBOX }, function(res, err){
    if(err || !res){
      mailboxBusy = false;
      if(cb) cb(null);
      return;
    }
    if(res.value===undefined || res.value===null){
      mailboxBusy = false;
      if(cb) cb(null);
      return;
    }

    let v=res.value;
    if(isStr(v)){
      try { v = JSON.parse(v); } catch(_e){ v = null; }
    }
    if(!v || typeof v !== 'object'){
      mailboxBusy = false;
      if(cb) cb(null);
      return;
    }

    // Clear mailbox immediately to avoid replays
    Shelly.call("KVS.Set", { key: KVS_MAILBOX, value: null }, function(){
      mailboxBusy = false;
      if(cb) cb(v);
    });
  });
}

function handleMailboxCmd(cmd){
  let grp = pickGroupList(cmd.group);
  let tok = tokenFromParams(cmd);
  if(!grp){
    if(DEBUG) print("bridge bad_group", JSON.stringify(cmd));
    return;
  }
  if(!tok){
    if(DEBUG) print("bridge bad_params", JSON.stringify(cmd));
    return;
  }
  sendTokenToList(tok, grp.list, grp.label);
}

function startPolling(){
  if(pollTimer) Timer.clear(pollTimer);
  pollTimer = Timer.set(POLL_MS, true, function(){
    readMailboxOnce(function(cmd){
      if(cmd) handleMailboxCmd(cmd);
    });
  });
}

// ---------- Startup ----------
reloadAll(function(){
  startPolling();
  print("Remote Bridge (KVS) ready. A:", A_IPS.length, "B:", B_IPS.length, "poll:", POLL_MS, "ms");
});