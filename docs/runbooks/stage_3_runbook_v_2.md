# Stage 3 Runbook (Provisioning / Shelly Gen2 & Gen3)

Dieses Runbook beschreibt Betrieb, Workflow und Fehleranalyse von **Stage 3** im Provisioning-Framework. Stage 3 kümmert sich um:

- OTA-Check & optionales Firmware-Update
- Synchronisation der Friendly Names von `ip_state.json` → Shelly
- Aktualisierung von Metadaten in `ip_state.json`

Stage 3 arbeitet ausschließlich auf Basis der offiziellen Shelly-RPC-Schnittstellen.

---

## 1. Dateien & Struktur

Projektstruktur (relevant für Stage 3):

```text
project-root/
  shelly_stage3.py             # CLI-Wrapper für Stage 3
  core/
    provision/
      stage3_core.py           # Kernlogik von Stage 3
  data/
    config.yaml                # zentrale Konfiguration
    ip_state.json              # Geräteliste + Metadaten
    secrets.yaml               # für Stage 3 aktuell nicht genutzt
```

### 1.1 Wichtige Dateien

- **`data/config.yaml`**
  - Enabling/Disabling Stage 3
  - OTA-Modus (check_only / check_and_update)
  - Friendly-Name-Modus (backfill/overwrite)
  - Logging-Konfiguration

- **`data/ip_state.json`**
  - Enthält alle bekannten Shelly-Geräte
  - Struktur:
    - Entweder flach: `{ "<mac>": { ... } }`
    - Oder mit Wrapper: `{ "version": 1, "devices": { "<mac>": { ... } } }`
  - Pro Device u. a. Felder:
    - `ip`, `model`, `fw`, `hostname`
    - `friendly_name` (oder anderes Feld, konfigurierbar)
    - `stage3`: OTA-/Friendly-Status

---

## 2. Konfiguration (config.yaml)

### 2.1 Stage-3-Abschnitt

Beispielkonfiguration:

```yaml
stage3:
  enabled: true

  ip_state_file: data/ip_state.json

  ota:
    enabled: true
    mode: check_and_update   # oder: check_only
    timeout: 20              # Sekunden für OTA-RPCs

  friendly:
    enabled: true
    field_name: friendly_name
    backfill: false          # false => JSON ist Master, Device folgt

  logging:
    base_path: data/stage3_log.txt
```

### 2.2 Bedeutung der Friendly-Optionen

- `enabled: true`
  - Friendly-Handling ist aktiv.

- `field_name: friendly_name`
  - Feld in `ip_state.json`, das als Friendly-Name-Quelle dient.

- `backfill: true`
  - Device-Name ist Master.
  - Verhalten:
    - Hat das Gerät bereits einen Namen → **nicht überschreiben**.
    - Hat das Gerät keinen Namen → Name aus JSON auf Device schreiben.

- `backfill: false`
  - JSON ist Master.
  - Verhalten:
    - Wenn im JSON ein Friendly-Name steht, wird er **immer** auf das Device geschrieben.
    - Bestehende Device-Namen werden überschrieben.

---

## 3. CLI-Befehle

### 3.1 Standardlauf

```bash
sudo python3 shelly_stage3.py
```

Effekt:
- Alle Devices in `ip_state.json` werden verarbeitet.
- OTA-Check / OTA-Update gemäß `ota.mode`.
- Friendly Names gemäß `friendly.backfill`.
- `ip_state.json` wird **persistiert** (mit Backup).

### 3.2 Dry-Run (keine Änderungen)

```bash
sudo python3 shelly_stage3.py --dry-run
```

- Nur RPC-Lesezugriffe.
- Keine OTA-Updates, kein Friendly-Name-Write.
- `ip_state.json` wird **nicht** geschrieben.

### 3.3 Nur bestimmte IPs

```bash
sudo python3 shelly_stage3.py --ip 192.168.1.30 192.168.1.31
```

- Nur Devices mit diesen IPs werden verarbeitet.

### 3.4 Nur online-Geräte anzeigen

```bash
sudo python3 shelly_stage3.py --online
```

- Geräte mit `OTA=offline` werden in der Ausgabe unterdrückt.
- Die Verarbeitung selbst berücksichtigt weiterhin alle Geräte.

### 3.5 Quiet-Mode

```bash
sudo python3 shelly_stage3.py --quiet
```

- Unterdrückt alle per-Device-Ausgaben.
- Nur Summary & Fehler werden ausgegeben.

---

## 4. CLI-Ausgabe & Farbcodes

Stage 3 druckt pro Gerät genau **eine Zeile**, typischerweise <80 Zeichen.

Beispiele:

```text
● S2PMG3 @ 192.168.1.35 - OTA=up_to_date | Friendly=ok (Wohnzimmer)
● S1MINIPMG3 @ 192.168.1.78 - OTA=updateable | Friendly=no_value
● S2PMG3 @ 192.168.1.51 - OTA=offline
● I4G3 @ 192.168.1.30 - OTA=up_to_date | Friendly=error (Name) | ERR=friendly: HTTP 500
```

Farben:

- **Punkt / OTA=...**
  - Grün: `OTA=up_to_date` / `OTA=skipped`
  - Gelb: `OTA=updateable` (Update verfügbar / angestoßen)
  - Rot: `OTA=offline`, `OTA=check_failed`, `OTA=error`

Friendly-Teil:

- `Friendly=ok (Name)`
- `Friendly=no_value` (kein Friendly-Name im JSON)
- `Friendly=error (Name) | ERR=...` (Fehler beim Friendly-Handling)

Am Ende:

```text
Stage 3 summary: total=X ok=Y failed=Z
```

`ok` ist dann `True`, wenn kein Gerät einen harten Fehler hatte (OTA/Friendly).

---

## 5. Ablauf im Core (stage3_core.py)

### 5.1 Schritte pro Device

Für jedes Device (MAC) aus `ip_state.json`:

1. **Reachability** prüfen
   - `ping_ip(ip, timeout=0.25s)`
   - Fallback: `Shelly.GetStatus` / `Sys.GetStatus` mit HTTP-Timeout 1s
   - Bei Fehlschlag: `ota_status="offline"`, Friendly bleibt unverändert.

2. **OTA-Handling** (wenn `ota.enabled: true`)
   - `Shelly.CheckForUpdate` via `/rpc/Shelly.CheckForUpdate`
     - Kein Update → `ota_status="up_to_date"`
     - Update verfügbar → `ota_status="update_available"`
   - Wenn `mode: check_and_update` und Update verfügbar und **kein** `--dry-run`:
     - `Shelly.Update` via `/rpc/Shelly.Update?stage=stable`
     - Der Update-Prozess läuft asynchron auf dem Gerät.

3. **Friendly-Handling** (wenn `friendly.enabled: true`)
   - Friendly aus JSON lesen (`friendly_name` oder `field_name` aus Config).
   - Wenn kein Friendly im JSON → `friendly_status="no_value"`.
   - Ansonsten:
     - Versuch von `Sys.GetConfig` (aktuell nicht mehr fatal bei Fehler).
     - Je nach `backfill`:
       - `backfill: true` → nur schreiben, wenn Device-Name leer.
       - `backfill: false` → immer JSON → Device schreiben.
     - Schreiben mit `Sys.SetConfig`.

4. **Status in `ip_state.json` aktualisieren**
   - Pro Device wird `stage3`-Block gepflegt:
     - `stage3.ota_status`
     - `stage3.friendly_status`
     - `stage3.last_run`

### 5.2 Parallelisierung

- Stage3 verarbeitet Devices parallel mit `ThreadPoolExecutor`.
- Default: `concurrency=8` (in `shelly_stage3.py` beim Aufruf gesetzt).
- Jedes Device erhält eine eigene `requests.Session`-Instanz.

---

## 6. OTA-Semantik

- `ota.enabled: false`
  - OTA-Handling wird komplett übersprungen.
  - `ota_status="skipped"`.

- `ota.mode: check_only`
  - Nur `Shelly.CheckForUpdate`, kein `Shelly.Update`.

- `ota.mode: check_and_update`
  - Wenn Update verfügbar und kein `--dry-run`:
    - `Shelly.Update` wird angestoßen.
    - Der Status bleibt für diesen Lauf bei `update_available`.
    - Beim nächsten Lauf, wenn kein Update mehr verfügbar ist, wird `ota_status="up_to_date"` gesetzt.

- Typische `ota_status`-Werte:
  - `up_to_date`
  - `update_available`
  - `offline`
  - `check_failed` / `error`
  - `skipped`

---

## 7. Friendly-Name-Semantik

### 7.1 Leseseite

- Friendly-Name-Sicht in Stage3:
  - JSON: `entry.friendly_name` (z. B. aus `friendly_name`)
  - Device: gelesen über `Sys.GetConfig` (`device.name`), wenn möglich.

- `Sys.GetConfig`-Fehler führen **nicht mehr** zu einem unmittelbaren Abbruch:
  - Der aktuelle Device-Name wird dann als "unbekannt" behandelt.
  - Friendly-Write kann trotzdem versucht werden.

### 7.2 Schreibseite (entscheidend)

Der eigentliche Write-Pfad sitzt in `set_device_name()`:

```python
url = f"http://{ip}/rpc/Sys.SetConfig"
payload = {"device": {"name": new_name}}
config_str = json.dumps(payload, separators=(",", ":"))
params = {"config": config_str}
```

- Wichtig: JSON wird mit `separators=(",", ":")` erzeugt → **keine Spaces**.
- Hintergrund: einige Shelly-Firmwares liefern bei JSON mit Spaces (z. B. `{"device": {"name": "X"}}`) HTTP 500.
- Die kompakten Strings (z. B. `{"device":{"name":"Test"}}`) funktionieren stabil.

### 7.3 Friendly-Statuswerte

- `ok` – Friendly-Use-Case erfolgreich verarbeitet:
  - Name war schon synchron, oder
  - Name wurde erfolgreich gesetzt.

- `no_value` – im JSON ist kein Friendly-Name gesetzt.

- `error` – Fehler beim Friendly-Handling:
  - z. B. HTTP 500 von `Sys.SetConfig`.
  - CLI zeigt dann `ERR=...` mit einer gekürzten Fehlermeldung.

---

## 8. Fehleranalyse & typische Szenarien

### 8.1 Gerät offline

CLI:

```text
● S1MINIPMG3 @ 192.168.1.54 - OTA=offline
```

- `ping` und/oder RPC nicht erreichbar.
- Maßnahmen:
  - Stromversorgung / Netzwerk prüfen.
  - IP möglicherweise veraltet → ip_state.json aktualisieren.

### 8.2 OTA-Check-Fehler

CLI:

```text
● S2PMG3 @ ... - OTA=error | Friendly=ok (Name) | ERR=OTA: HTTP 500...
```

- `Shelly.CheckForUpdate` oder `Shelly.Update` schlägt fehl.
- Maßnahmen:
  - Gerät direkt im Browser aufrufen.
  - Firmware-Stand und Update-Kanal prüfen.

### 8.3 Friendly=error

CLI:

```text
● I4G3 @ 192.168.1.30 - OTA=up_to_date | Friendly=error (Name) | ERR=friendly: HTTP 500
```

- `Sys.SetConfig` konnte den Namen nicht setzen.
- Mögliche Ursachen:
  - Firmware-Bug (z. B. intolerante JSON-Parser).
  - Ungültige Zeichen / Länge im Namen.

- Stage3-Patch:
  - Kompaktes JSON ohne Spaces (siehe oben) löst HTTP-500-Probleme bei manchen Gen3.

### 8.4 ip_state.json nicht schreibbar

- Symptome:
  - Fehlermeldung `cannot write state file ...`.
- Mögliche Ursachen:
  - Dateisystem read-only
  - Berechtigungen (root vs. normaler User)

- Maßnahmen:
  - Rechte prüfen.
  - Freien Speicherplatz prüfen.

---

## 9. Safe-Write von ip_state.json

Stage 3 schreibt `ip_state.json` sicher:

1. Bestehende Datei wird (falls vorhanden) nach `ip_state.json.bak` kopiert.
2. Neue Version wird zunächst als `ip_state.json.tmp` geschrieben.
3. Danach erfolgt ein atomarer `replace` von `.tmp` → endgültige Datei.

Vorteile:
- Schutz vor teilweise geschriebenen Dateien.
- Schnelle Recovery über `.bak` möglich.

---

## 10. Betriebsempfehlungen

- **Neue Konfigurationen / viele neue Geräte**
  - Zuerst immer: `--dry-run`.
  - Prüfen, ob Friendly und OTA-Status plausibel sind.

- **Regelbetrieb**
  - Stage 3 regelmäßig (z. B. per Cron) laufen lassen.
  - OTA-Modus je nach Risikobereitschaft:
    - `check_only` für rein informative Läufe.
    - `check_and_update` für automatisches Fleet-Update.

- **Naming-Policy**
  - Normalisierung und Validierung der Friendly Names vorzugsweise im Web-UI.
  - Stage 3 kann zusätzlich eine minimale technische Normalisierung implementieren (Längenlimit, printable chars).

- **Troubleshooting**
  - Bei `Friendly=error` oder `OTA=error` auf den `ERR=`-Teil achten.
  - Bei systemischen Problemen: Stage 3 mit `--quiet` und gezielten `--ip`-Runs verwenden.

---

Ende des Stage-3-Runbooks.

