# Runbook – Stage 1 Provisioning

## Purpose
Stage 1 provisions factory‑new Shelly Gen3 devices via their internal access point (AP). It configures WiFi, disables cloud, Bluetooth, local AP and MQTT if requested, and reboots the device into the production network.

Stage 1 normally runs in controlled environments where the operator’s workstation and the provisioning Raspberry Pi are on Ethernet, and the Pi uses its own WiFi interface to connect to the Shelly AP.

---

## Preconditions
- Device is in factory state or manually reset.
- Shelly AP visible as `Shelly*‑XXXXXXXXXXXX`.
- Raspberry Pi WiFi must be enabled and able to connect to the Shelly AP.
- `secrets.yaml` contains valid WiFi credentials.
- `config.yaml` defines Stage 1 runtime behaviour (paths, logging, options).

---

## Files & Configuration
### secrets.yaml
Contains only secrets, e.g.:
- WiFi SSIDs + passwords
- Optional MQTT credentials

### config.yaml – Stage 1 section
Controls:
- Whether Stage 1 is enabled
- AP IP (default 192.168.33.1)
- Options to disable cloud/BLE/AP/MQTT
- Loop mode (for provisioning many devices)
- Logging paths (relative to project root)

### shelly_stage1.py
Wrapper around `core.provision.stage1_ap_core` providing:
- CLI interface
- Log handling
- Session execution
- Result summarisation

---

## Workflow
1. **Wait for Shelly AP** (unless `--dry-run`).
2. **Connect to AP** via Raspberry Pi WLAN.
3. **Query system information** via RPC.
4. **Apply configuration**:
   - Set target WiFi SSID + password
   - Disable unwanted services (cloud/AP/BLE/MQTT)
   - Commit configuration
5. **Reboot device** into target WiFi.
6. **Wait for device to appear online** on production network.
7. **Persist adoption entry** for Stage 2 (if configured).
8. **Loop** (if `loop_mode: true`).

---

## CLI Usage
```
sudo python3 shelly_stage1.py [-f SECRETS] [--dry-run] [--log LOGFILE]
```

### Options
- `-f, --config` – path to secrets.yaml
- `--dry-run` – simulate only, no WiFi switching or RPC writes
- `--log` – override logging path

---

## Example Output
```
[config: loaded file=data/secrets.yaml dry_run=False]
[stage1: waiting for Shelly AP]
[stage1: connected to Shelly AP]
[rpc: read device info]
[rpc: apply WiFi + disable cloud/ap/mqtt]
[rpc: rebooting]
[stage1: device joined WiFi at 192.168.1.183]
```

---

## Typical Errors & Resolutions
### 1. AP unreachable
**Symptoms:**
- `ConnectTimeout` when calling `Sys.GetStatus`.
**Fix:**
- Ensure Raspberry Pi WiFi is enabled and not bound to your normal WLAN.

### 2. Device reboots every ~90 s
**Cause:**
- Observed behaviour on some I4 units in partially configured state.
**Fix:**
- Perform a *10 s reset (short)*, not the *factory reset (long)*.

### 3. WiFi password required before manual static‑IP save
**Relevance:**
- Stage 1 passes SSID + password correctly; manual config is not needed.

### 4. Loop mode traps user
- When `loop_mode: true`, Stage 1 waits for the next device indefinitely.
**Fix:**
- Use CLI `Ctrl+C`, or disable in config.yaml for GUI use.

---

## Operational Notes
- Stage 1 should run *exclusively*; no parallel Stage 2 or Web‑UI provisioning.
- Logs are written relative to project root (`var/log/`).
- After Stage 1 completes, the device is ready for Stage 2 IP assignment.

---

## Next Steps
- Run Stage 2 for IP assignment and naming.
- Use the Web‑UI or CLI for inventory and review.

---

End of Document.

