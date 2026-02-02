# Runbook: shelly_report.py

## 1. Überblick
`shelly_report.py` ist ein reines Offline-Werkzeug zur Auswertung und Dokumentation von Shelly-Geräten auf Basis der Datei:

```
data/ip_state.json
```

Die Datei ist **Single Source of Truth** und wird ausschließlich gelesen.

Alle Ausgabeformate (stdout‑Report, CSV-Exports, Label-Dateien) werden durch `data/config.yaml` gesteuert.

Keine Kommandos greifen online auf Shellys zu.

---

## 2. Voraussetzungen
- Python 3.9 oder neuer
- Dateien und Struktur:
  - `data/config.yaml` (mit einem `report:`-Block)
  - `data/ip_state.json` (Gerätebestand)
  - Output-Verzeichnisse:
    - `data/report/` (für Tabellen-Exporte)
    - `data/labels/` (für Label-Generator)

Start des Tools:
```
./shelly_report.py <subcommand> [options]
```

---

## 3. Subcommands

### 3.1. `report`
Gibt eine sortierte Gerätetabelle auf stdout aus.

Beispiel:
```
./shelly_report.py report
```

Mit Filter:
```
./shelly_report.py report --filter done
```

Mit eigenen Spalten:
```
./shelly_report.py report --columns location room model ip friendly_name fw
```

Sortieren:
```
./shelly_report.py report --sort location room -model
```

Verfügbare Filter:
- `all`
- `friendly_ok`
- `ota_ok`
- `script_ok`
- `done`
- `error_only`

### 3.2. `export`
Exportiert eine CSV für Excel.

Beispiel:
```
./shelly_report.py export
```

Eigener Dateiname:
```
./shelly_report.py export --basename shelly_list
```

Eigene Spalten:
```
./shelly_report.py export --columns id ip hostname model fw
```

Sortierung:
```
./shelly_report.py export --sort room friendly_name
```

CSV wird geschrieben nach:
```
data/report/<basename>.csv
```

### 3.3. `labels`
Generator für DYMO‑kompatible CSV-Dateien.

Beispiel (Default-Template):
```
./shelly_report.py labels
```

Band‑Labels:
```
./shelly_report.py labels --mode band --template dymo_band_standard
```

Multiline‑Labels:
```
./shelly_report.py labels --mode multiline --template dymo_multiline_default
```

Sortierung für Labels:
```
./shelly_report.py labels --sort location friendly_name
```

Output landet unter:
```
data/labels/
```

---

## 4. Sortierung
Sortierreihenfolge kann kommen aus:
- `config.yaml` → `report.sort.default_order`
- CLI → `--sort`

Beispiele:
```
--sort location room model
--sort -room
--sort location -model friendly_name
```

---

## 5. Konfiguration (`config.yaml`)
Beispielhafter `report:`-Block:

```yaml
report:
  enabled: true
  state_file: "data/ip_state.json"

  output:
    table_dir: "data/report"
    labels_dir: "data/labels"

  sort:
    default_order:
      - location
      - room
      - model
      - friendly_name

  stdout:
    default_filter: "all"
    default_columns:
      - location
      - room
      - model
      - ip
      - friendly_name
      - fw

  export:
    default_format: "csv"
    csv_delimiter: ";"
    default_columns:
      - id
      - ip
      - hostname
      - model
      - fw
      - room
      - location
      - stage3_friendly_status
      - stage3_ota_status
      - stage4_status_result

  labels:
    default_mode: "multiline"
    default_basename: "shelly_labels"

    templates:
      dymo_band_standard:
        type: "band"
        text: "{location} {room} {friendly_name} {ip}"

      dymo_multiline_default:
        type: "multiline"
        fields:
          line1: "{location} {room}"
          line2: "{friendly_name}"
          line3: "{ip}"
          line4: "{model}"
```

---

## 6. Häufige Anwendungsfälle

### Alle Geräte sortiert ausgeben:
```
./shelly_report.py report --sort location room friendly_name
```

### Nur fertige Geräte für Excel exportieren:
```
./shelly_report.py export --filter done --basename fertig
```

### Kabel‑Bandlabels für den Elektriker:
```
./shelly_report.py labels --mode band --template dymo_band_standard
```

### Raum‑Gruppenlabels erzeugen:
```
./shelly_report.py labels --sort room friendly_name
```

---

## 7. Troubleshooting

### "Missing 'report:' section"
Die `config.yaml` muss einen `report:`-Block enthalten.

### "ip_state file not found"
Pfad in `config.yaml → report.state_file` prüfen.

### Leere Felder in Labels
Felder mit `{xyz}` werden leer, wenn das Gerät das Attribut nicht hat.

### Falsche Sortierung
Entweder `--sort` explizit setzen oder `config.yaml → report.sort.default_order` prüfen.

---

## 8. Pflege & Weiterentwicklung
- Neue Felder jederzeit in `ip_state.json` möglich.
- Parser in `build_devices_from_state()` ist die einzig zentrale Stelle, die bei Schemaänderungen angepasst werden muss.
- Neue Label‑Templates können in `config.yaml` ergänzt werden.
- XLSX‑Export kann später ergänzt werden.

---

Ende des Runbooks.

