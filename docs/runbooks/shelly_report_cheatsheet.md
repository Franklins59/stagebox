# Shelly Report – Cheatsheet

Kurzreferenz für `shelly_report.py` (Offline-Tool)

---

## Basis
Start:
```
./shelly_report.py <command> [options]
```

Eingabedatei:
```
data/ip_state.json
```

Konfiguration:
```
data/config.yaml → report:
```

---

## Commands

### 1. REPORT (stdout)
Einfacher Überblick am Terminal.
```
./shelly_report.py report
```

**Filter:**
```
--filter all|friendly_ok|ota_ok|script_ok|done|error_only
```

**Sortierung:**
```
--sort location room model
--sort -room
--sort location -model friendly_name
```

**Eigene Spalten:**
```
--columns location room model ip friendly_name fw
```

---

### 2. EXPORT (CSV für Excel)
```
./shelly_report.py export
```

**Eigener Dateiname:**
```
--basename shelly_liste
```

**Eigene Spalten:**
```
--columns id ip hostname model fw
```

**Sortierung:**
```
--sort ip
```

Output:
```
data/report/<basename>.csv
```

---

### 3. LABELS (für Dymo)
```
./shelly_report.py labels
```

**Templates (aus config.yaml):**
- `dymo_band_standard` (einzeilig)
- `dymo_multiline_default` (mehrzeilig)

**Band-Label:**
```
./shelly_report.py labels --mode band --template dymo_band_standard
```

**Multiline:**
```
./shelly_report.py labels --mode multiline --template dymo_multiline_default
```

**Sortierung:**
```
--sort location friendly_name
```

Output:
```
data/labels/
```

---

## Filter-Definition
- **all**: keine Einschränkung
- **friendly_ok**: Stage 3 Friendly Script ok
- **ota_ok**: Firmware up_to_date
- **script_ok**: Stage 4 Script ok
- **done**: alles ok (friendly + ota + script)
- **error_only**: mindestens ein Fehler

---

## Nützliche Beispiele

### Übersicht aller Geräte nach Standort sortiert:
```
./shelly_report.py report --sort location room
```

### Geräte mit Fehlern anzeigen:
```
./shelly_report.py report --filter error_only
```

### CSV aller fertigen Geräte:
```
./shelly_report.py export --filter done --basename fertig
```

### Bandlabels für Elektriker:
```
./shelly_report.py labels --mode band --template dymo_band_standard
```

### Labels gruppiert nach Raum:
```
./shelly_report.py labels --sort room friendly_name
```

---

## Wichtig
- **Keine Online-Abfragen** (reines Offline-Tool)
- **ip_state.json niemals verändern**
- Anpassungen am JSON-Schema → nur `build_devices_from_state()` muss geändert werden

---

Fertig.

