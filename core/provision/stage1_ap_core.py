
# Comments in English.
#
# Shelly Gen3 provisioning core.
#
# Changes in this revision:
# - When no AP is actually connectable, we log a friendly
#   "[status: no new shelly ready]" instead of "[connect: FAILED all]".
# - We ensure a blank line is written after each completed device
#   AND after a "no new shelly ready" cycle (console + global log + per-device log if known).
#
# Other behavior kept:
# - Scan all Shelly-* APs (sorted by signal), try to connect strongest-first
# - Apply WiFi creds, disable cloud/ble/ap/mqtt, reboot
# - Disconnect WiFi interface at the end to avoid sticky NM state
# - One line per event: "[action: result]"
# - Per-device logfile "<session>_<MAC>.log"
#
import subprocess
import time
import json
import requests
from datetime import datetime
import os

# Placeholder SSIDs that should be ignored (from secrets.yaml.example or incomplete config)
PLACEHOLDER_SSIDS = {
    "", "SSID", "SSID2", "YOUR_SSID", "YOUR_BACKUP_SSID",
    "YOUR_WIFI_SSID", "BACKUP_SSID", "EXAMPLE_SSID",
}


def _is_placeholder_ssid(ssid: str) -> bool:
    """Check if SSID is a placeholder that should be ignored."""
    if not ssid:
        return True
    return ssid.strip().upper() in {s.upper() for s in PLACEHOLDER_SSIDS}


def _run_cmd(cmd, timeout=10):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return 1, str(e)

def _detect_wifi_iface():
    rc, out = _run_cmd(["nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status"])
    if rc != 0:
        return None
    for line in out.splitlines():
        parts = line.strip().split(":")
        if len(parts) >= 2:
            dev, typ = parts[0].strip(), parts[1].strip()
            if typ == "wifi" and dev:
                return dev
    return None

def wifi_disconnect(iface_hint=None):
    iface = iface_hint or _detect_wifi_iface()
    if not iface:
        return False
    rc, out = _run_cmd(["nmcli", "device", "disconnect", iface])
    return rc == 0

def scan_shelly_aps(interface_hint=None):
    cmd = ["nmcli", "-t", "-f", "SSID,SECURITY,SIGNAL", "device", "wifi", "list"]
    if interface_hint:
        cmd += [interface_hint]
    rc, out = _run_cmd(cmd)
    aps = []
    if rc != 0:
        return aps
    seen = set()
    for line in out.splitlines():
        parts = line.strip().split(":")
        if len(parts) < 3:
            continue
        ssid, sec, sig = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not ssid:
            continue
        if ssid.lower().startswith("shelly"):
            if ssid not in seen:
                try:
                    sig_val = int(sig)
                except:
                    sig_val = None
                aps.append({"ssid": ssid, "security": sec, "signal": sig_val})
                seen.add(ssid)
    aps.sort(key=lambda x: (x["signal"] if x["signal"] is not None else -999), reverse=True)
    return aps

def connect_open_ap(ssid, iface=None, dry_run=False):
    if dry_run:
        return True
    cmd = ["nmcli", "device", "wifi", "connect", ssid]
    if iface:
        cmd += ["ifname", iface]
    rc, out = _run_cmd(cmd, timeout=20)
    time.sleep(2)
    return rc == 0

def _http_get(ip, path, timeout=4):
    url = f"http://{ip}{path}"
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.text, r.headers.get("content-type","")
    except Exception as e:
        return None, str(e), ""

def _http_post(ip, path, payload, timeout=4):
    url = f"http://{ip}{path}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r.status_code, r.text, r.headers.get("content-type","")
    except Exception as e:
        return None, str(e), ""

def _http_put(ip, path, payload, timeout=4):
    url = f"http://{ip}{path}"
    try:
        r = requests.put(url, json=payload, timeout=timeout)
        return r.status_code, r.text, r.headers.get("content-type","")
    except Exception as e:
        return None, str(e), ""

def probe_device_info(ip):
    candidates = ["/rpc/Shelly.GetInfo", "/rpc/Shelly.GetDeviceInfo", "/rpc/Shelly.GetStatus", "/settings"]
    for p in candidates:
        code, text, ctype = _http_get(ip, p)
        if code == 200:
            try:
                data = json.loads(text)
                data["_probe_path"] = p
                return data
            except Exception:
                continue
    return {}

def get_settings_sta(ip, slot):
    candidates = [f"/settings/sta{slot}", f"/rpc/WiFi.GetSta?slot={slot}", "/settings"]
    for p in candidates:
        code, text, ctype = _http_get(ip, p)
        if code == 200:
            try:
                return json.loads(text)
            except Exception:
                continue
    return None

def _gen_sta_payloads_for_slot(slot, ssid, password):
    if slot == 1:
        keys = ["sta", "sta0", "sta1"]
    else:
        keys = ["sta1", "sta2"]
    candidates = []
    for k in keys:
        candidates.append(("/rpc/WiFi.SetConfig", {"config": {k: {"ssid": ssid, "pass": password, "enable": True}}}))
        candidates.append(("/rpc/WiFi.SetConfig", {"config": {k: {"ssid": ssid, "password": password, "enable": True}}}))
        candidates.append(("/rpc/WiFi.SetConfig", {"config": {k: {"ssid": ssid, "psk": password, "enable": True}}}))
    return candidates

def _legacy_sta_payloads_for_slot(slot, ssid, password):
    cands = []
    cands.append(("/rpc/WiFi.SetSta", {"ssid": ssid, "password": password, "enabled": True, "slot": slot}))
    cands.append(("/rpc/WiFi.SetSta", {"ssid": ssid, "password": password, "enabled": True}))
    cands.append(("/rpc/WiFi.SetSta", {"sta": {"ssid": ssid, "password": password, "enabled": True, "slot": slot}}))
    cands.append((f"/settings/sta{slot}", {"ssid": ssid, "password": password}))
    cands.append((f"/settings/sta{slot}", {"wifi": {"sta": {"ssid": ssid, "password": password}}}))
    cands.append(("/settings", {"sta": {f"sta{slot}": {"ssid": ssid, "password": password}}}))
    cands.append((f"/settings/sta{slot}", {"ssid": ssid, "psk": password}))
    return cands

def _try_payload_candidates(ip, candidates, attempts_accum):
    success = False
    for (path, payload) in candidates:
        code, text, ctype = _http_post(ip, path, payload)
        attempts_accum.append({"method":"POST","path":path,"status":code})
        if code and 200 <= code < 300:
            success = True
            break
        code2, text2, ctype2 = _http_put(ip, path, payload)
        attempts_accum.append({"method":"PUT","path":path,"status":code2})
        if code2 and 200 <= code2 < 300:
            success = True
            break
        time.sleep(0.15)
    return success, attempts_accum

def _set_one_sta_slot(ip, slot, ssid, password):
    attempts = []
    success = False
    gen3_candidates = _gen_sta_payloads_for_slot(slot, ssid, password)
    success, attempts = _try_payload_candidates(ip, gen3_candidates, attempts)
    if not success:
        legacy_candidates = _legacy_sta_payloads_for_slot(slot, ssid, password)
        success, attempts = _try_payload_candidates(ip, legacy_candidates, attempts)
    verification = None
    if success:
        time.sleep(0.5)
        verification = get_settings_sta(ip, slot)
    return {"slot": slot, "success": success, "verification": verification, "attempts": attempts}

def set_sta_slots(ip, wifi_profiles, dry_run=False):
    results = []
    slot_num = 1
    for prof in wifi_profiles:
        ssid = prof.get("ssid","")
        pw   = prof.get("password","")
        # Skip empty or placeholder SSIDs
        if _is_placeholder_ssid(ssid):
            slot_num += 1
            continue
        if dry_run:
            results.append({"slot": slot_num, "ssid": ssid, "success": True})
        else:
            r = _set_one_sta_slot(ip, slot_num, ssid, pw)
            results.append({"slot": slot_num, "ssid": ssid, "success": r["success"]})
        slot_num += 1
    return results

def _simple_success_from_attempts(attempts):
    for a in attempts:
        st = a.get("status")
        if st and 200 <= st < 300:
            return True
    return False

def disable_cloud(ip, dry_run=False):
    attempts = []
    candidate_payloads = [
        ("/rpc/Cloud.SetConfig", {"config": {"enable": False}}),
        ("/rpc/Cloud.SetState", {"config": {"enable": False}}),
        ("/settings/cloud", {"enable": False}),
        ("/settings", {"cloud": {"enable": False}}),
    ]
    if dry_run:
        return {"success": True}
    for path, payload in candidate_payloads:
        code, text, ct = _http_post(ip, path, payload)
        attempts.append({"method":"POST","path":path,"status":code})
        if code and 200 <= code < 300:
            break
    return {"success": _simple_success_from_attempts(attempts)}

def disable_bluetooth(ip, dry_run=False):
    attempts = []
    candidate_payloads = [
        ("/rpc/Ble.SetConfig", {"config": {"enable": False}}),
        ("/rpc/Bluetooth.SetConfig", {"config": {"enable": False}}),
        ("/rpc/BLE.SetConfig", {"config": {"enable": False}}),
        ("/settings/bluetooth", {"enable": False}),
        ("/settings", {"bluetooth": {"enable": False}}),
    ]
    if dry_run:
        return {"success": True}
    for path, payload in candidate_payloads:
        code, text, ct = _http_post(ip, path, payload)
        attempts.append({"method":"POST","path":path,"status":code})
        if code and 200 <= code < 300:
            break
    return {"success": _simple_success_from_attempts(attempts)}

def disable_ap(ip, dry_run=False):
    attempts = []
    candidate_payloads = [
        ("/rpc/WiFi.SetConfig", {"config": {"ap": {"enable": False}}}),
        ("/rpc/WiFi.SetAp", {"enabled": False}),
        ("/settings/ap", {"enabled": False}),
        ("/settings", {"ap": {"enabled": False}}),
    ]
    if dry_run:
        return {"success": True}
    for path, payload in candidate_payloads:
        code, text, ct = _http_post(ip, path, payload)
        attempts.append({"method":"POST","path":path,"status":code})
        if code and 200 <= code < 300:
            break
    return {"success": _simple_success_from_attempts(attempts)}

def disable_mqtt(ip, dry_run=False):
    attempts = []
    candidate_payloads = [
        ("/rpc/MQTT.SetConfig", {"config": {"enable": False}}),
        ("/settings/mqtt", {"enable": False}),
        ("/settings", {"mqtt": {"enable": False}}),
    ]
    if dry_run:
        return {"success": True}
    for path, payload in candidate_payloads:
        code, text, ct = _http_post(ip, path, payload)
        attempts.append({"method":"POST","path":path,"status":code})
        if code and 200 <= code < 300:
            break
    return {"success": _simple_success_from_attempts(attempts)}

def reboot(ip, dry_run=False):
    attempts = []
    if dry_run:
        return {"success": True}
    paths = [
        ("/rpc/Shelly.Reboot", {}),
        ("/rpc/Device.Reboot", {}),
        ("/reboot", {}),
    ]
    for path, payload in paths:
        code, text, ct = _http_post(ip, path, payload)
        attempts.append({"method":"POST","path":path,"status":code})
    return {"success": _simple_success_from_attempts(attempts)}

def _append_line_to_file(path, textline):
    if not path:
        return
    ts = datetime.utcnow().isoformat() + "Z"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {textline}\n")

def _append_blank_line_to_file(path):
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n")

def _compute_per_device_logfile(base_path, mac):
    if not base_path or not mac:
        return None
    root, ext = os.path.splitext(base_path)
    if not root:
        root = base_path
        ext = ""
    return root + "_" + mac + (ext if ext else ".log")

#def provision_once(config, dry_run=False, logfile=None, iface_hint=None):
def provision_once(config, dry_run=False, logfile=None, iface_hint=None, quiet=False):
    per_device_file = {"path": None}

    def log_event(action, result):
        line = f"[{action}: {result}]"
        if not quiet:
            print(line)
        _append_line_to_file(logfile, line)
        _append_line_to_file(per_device_file["path"], line)

    def log_blank():
        if not quiet:
            print("")
        _append_blank_line_to_file(logfile)
        _append_blank_line_to_file(per_device_file["path"])

    aps = scan_shelly_aps(interface_hint=iface_hint)
    if not aps:
        log_event("status", "no new shelly ready")
        disc_ok = wifi_disconnect(iface_hint)
        log_event("wifi_disconnect", f"success={disc_ok}")
        log_blank()
        return {"ok": False, "reason": "no_shelly_found", "aps": []}

    chosen_ap = None
    for cand in aps:
        ssid_try = cand["ssid"]
        log_event("scan", f"candidate {ssid_try} signal={cand['signal']}")
        ok_conn = connect_open_ap(ssid_try, iface=iface_hint, dry_run=dry_run)
        if ok_conn:
            chosen_ap = cand
            log_event("connect", f"ok {ssid_try}")
            break
        else:
            log_event("connect", f"FAILED {ssid_try}")

    if not chosen_ap:
        log_event("status", "no new shelly ready")
        disc_ok = wifi_disconnect(iface_hint)
        log_event("wifi_disconnect", f"success={disc_ok}")
        log_blank()
        return {"ok": False, "reason": "no_connectable_ap", "aps": aps}

    ssid = chosen_ap["ssid"]

    shelly_ip = config.get("shelly_ip", "192.168.33.1")
    time.sleep(2.0)
    info = probe_device_info(shelly_ip)
    if not info:
        time.sleep(1.0)
        info = probe_device_info(shelly_ip)
    mac   = info.get("mac") if isinstance(info, dict) else None
    model = info.get("model") if isinstance(info, dict) else None
    fw    = info.get("ver") if isinstance(info, dict) else None

    if logfile:
        per_device_file["path"] = _compute_per_device_logfile(logfile, mac or "unknownMAC")

    log_event("device", f"mac={mac} model={model} fw={fw}")

    wifi_profiles = config.get("wifi_profiles", [])
    slot_results = []
    if wifi_profiles:
        slot_results = set_sta_slots(shelly_ip, wifi_profiles, dry_run=dry_run)
        for r in slot_results:
            log_event(f"wifi_slot{r['slot']}", f"{r['ssid']} success={r['success']}")
    else:
        log_event("wifi", "NO PROFILES IN YAML")

    opts = config.get("options", {})

    if opts.get("disable_cloud", False):
        cloud_res = disable_cloud(shelly_ip, dry_run=dry_run)
        log_event("cloud_disable", f"success={cloud_res['success']}")

    if opts.get("disable_bluetooth", False):
        ble_res = disable_bluetooth(shelly_ip, dry_run=dry_run)
        log_event("ble_disable", f"success={ble_res['success']}")

    if opts.get("disable_ap", False):
        ap_res = disable_ap(shelly_ip, dry_run=dry_run)
        log_event("ap_disable", f"success={ap_res['success']}")

    if opts.get("mqtt_disable", False):
        mqtt_res = disable_mqtt(shelly_ip, dry_run=dry_run)
        log_event("mqtt_disable", f"success={mqtt_res['success']}")

    rb_res = reboot(shelly_ip, dry_run=dry_run)
    log_event("reboot", f"success={rb_res['success']}")

    disc_ok = wifi_disconnect(iface_hint)
    log_event("wifi_disconnect", f"success={disc_ok}")

    summary = {
        "ok": True,
        "ssid": ssid,
        "mac": mac,
        "model": model,
        "fw": fw,
        "wifi_profiles_written": [p.get("ssid") for p in wifi_profiles],
        "slot_results": slot_results,
        "dry_run": dry_run,
    }
    log_event("done", f"ok mac={mac}")
    log_blank()

    return summary

# provision_loop can be deleted!
def provision_loop(config, dry_run=False, logfile=None, iface_hint=None, sleep_no_ap=10, quiet=False):
    results = []
    if not quiet:
        print("[mode: loop]")
    while True:
        res = provision_once(
            config,
            dry_run=dry_run,
            logfile=logfile,
            iface_hint=iface_hint,
            quiet=quiet,
        )
        results.append(res)
        time.sleep(sleep_no_ap)
