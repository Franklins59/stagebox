# Stage 1 Cheatsheet – Shelly AP Provisioning

Stage 1 is responsible for the **initial provisioning via AP** of Gen3 Shelly devices:

- Connects to the Shelly AP (`192.168.33.1` by default)
- Pushes WiFi credentials from `secrets.yaml`
- Disables cloud / BLE / AP / MQTT (according to config)
- Reboots the device so it joins the main WiFi

---

## 1. Files involved

- **`data/config.yaml`**
  - Global settings for Stage 1 and the other stages
  - Stage-1-specific block:

    ```yaml
    stage1:
      enabled: true

      # Optional override for Shelly AP IP; if omitted, a top-level default may be used.
      shelly_ip: "192.168.33.1"

      options:
        disable_cloud: true
        disable_bluetooth: true
        disable_ap: true
        mqtt_disable: true
        loop_mode: true   # only respected in CLI, *not* in web-UI

      logging:
        base_path: "var/log/stage1_session.log"
        inventory: "var/log/stage1_inventory.csv"
    ```

- **`data/secrets.yaml`**
  - Holds **WiFi credentials** used during provisioning:

    ```yaml
    wifi_profiles:
      - ssid: "IoT"
        password: "xxxxx"
      - ssid: "FORSTEC2"
        password: "yyyyyy"
    ```

---

## 2. Basic CLI usage

Run Stage 1 once (no loop):

```bash
cd ~/stagebox
python3 shelly_stage1.py
```

With explicit config file (if you don’t use the default):

```bash
python3 shelly_stage1.py -f data/config.yaml
```

View help:

```bash
python3 shelly_stage1.py -h
```

Typical output (single device):

```text
[config: loaded file=/home/.../data/config.yaml dry_run=False]
[config: session_log=var/log/stage1_session.log]
[scan: candidate Shelly2PMG3-E4B3231B32D0 signal=100]
[connect: ok Shelly2PMG3-E4B3231B32D0]
[device: mac=E4B3231B32D0 model=S3SW-002P16EU fw=1.7.1]
[wifi_slot1: IoT success=True]
[wifi_slot2: FORSTEC2 success=True]
[cloud_disable: success=True]
[ble_disable: success=True]
[ap_disable: success=True]
[mqtt_disable: success=True]
[reboot: success=True]
[wifi_disconnect: success=True]
[done: ok mac=E4B3231B32D0]
```

---

## 3. Options & behaviour

### 3.1 Command-line options

```text
usage: shelly_stage1 [-h] [-f CONFIG] [--dry-run] [--log LOGFILE]

Stage 1: provision Shelly Gen3 devices via AP (WiFi, disable
cloud/BLE/AP/MQTT, reboot).

options:
  -h, --help           Show help and exit
  -f, --config CONFIG  YAML config file (default: data/config.yaml)
  --dry-run            Simulate only (no WiFi connect, no HTTP POST).
  --log LOGFILE        Override session log path (bypasses config.yaml).
```

### 3.2 Config-driven behaviour

- **`stage1.enabled`**
  - If `false`, the script exits immediately.
- **`stage1.shelly_ip`**
  - IP address of the Shelly AP (default 192.168.33.1).
- **`stage1.options.loop_mode`**
  - In CLI: if `true`, Stage 1 keeps scanning for new Shelly APs until you stop it.
  - In Web-UI (später): *nicht* aktiv, um den Browser nicht zu blockieren.
- **Logging**
  - `logging.base_path` – session log file (text)
  - `logging.inventory` – optional CSV with per-device records (if implemented)

---

## 4. Typical workflow

1. **Neuen Shelly in AP-Mode bringen**
   - Gerät resetten gemäß Shelly-Doku
   - AP „Shelly…“ sollte sichtbar sein.

2. **Stage 1 ausführen**
   - Sicherstellen, dass `wifi_profiles` in `secrets.yaml` korrekt sind.
   - `python3 shelly_stage1.py` starten.

3. **Warten bis Reboot**
   - Shelly verbindet sich mit `IoT` (oder dem ersten passenden WLAN-Profil).

4. **Weiter mit Stage 2**
   - Der Shelly sollte jetzt via DHCP im Hauptnetz sichtbar sein.
   - Stage 2 übernimmt IP-Pool-Zuordnung und Hostnamen.

---

## 5. Troubleshooting

**Problem:** Stage 1 findet keinen AP.
- Prüfen, ob der Shelly wirklich im AP-Modus ist (SSID „Shelly…“ sichtbar?)
- Prüfen, ob der Raspi-WLAN-Adapter korrekt konfiguriert ist.

**Problem:** Stage 1 bricht mit WiFi-/HTTP-Fehlern ab.
- Prüfen, ob `stage1.shelly_ip` mit dem tatsächlichen AP-IP übereinstimmt.
- `--dry-run` testen, um reine Logik/Parsing-Fehler auszuschließen.

**Problem:** Shelly rebootet alle 90s / instabil nach Stage 1.
- Ggf. 10s-Hard-Reset am I4 durchführen (ohne die „LED-blinkt-schnell“-Variante).
- Danach Stage 1 erneut laufen lassen.

---

Dieses Cheatsheet ist bewusst kompakt gehalten. Für tiefergehende technische Details und Fehlerbilder bietet sich ein eigenes Runbook in `docs/runbooks/` an (z. B. `stage1_runbook.md`).

