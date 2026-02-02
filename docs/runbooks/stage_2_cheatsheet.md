# Stage 2 Cheatsheet
Kompakte Referenz für Betrieb und Troubleshooting von **Stage 2** (Shelly DHCP / Network Provisioning).

---

## 1. Zweck von Stage 2
Stage 2 übernimmt die grundlegende Netzwerk-Provisionierung neu gefundener Shelly-Geräte:

- Lesen und Aktualisieren von IP/Hostname
- Überprüfen der Gerätemodelle
- Erfassen von Firmware- und Statusdaten
- Schreiben der Daten in `ip_state.json`

Stage 2 hat **keine OTA-Funktion** und **keine Friendly-Name-Synchronisation**.

---

## 2. Eingabedateien & Struktur

### `data/ip_state.json`
- Geräteliste
- Enthält MAC, IP, Model, Hostname, Firmware, Stage2-Metadaten

### `data/config.yaml`
- `stage2:`-Konfiguration
- Timeout-Parameter
- Logging

---

## 3. CLI-Befehle

### Standardlauf
```bash
sudo python3 shelly_stage2.py
```
- Scannt alle Devices aus `ip_state.json`
- Aktualisiert Hostname, Firmware, Model

### Dry-Run (keine Änderungen)
```bash
sudo python3 shelly_stage2.py --dry-run
```

### Nur bestimmte IPs
```bash
sudo python3 shelly_stage2.py --ip 192.168.1.50
```

### Quiet-Mode
```bash
sudo python3 shelly_stage2.py --quiet
```

---

## 4. Typischer Ablauf

1. **Ping / Online-Check** des Geräts
2. `Shelly.GetStatus` und `Sys.GetConfig` lesen
3. Modellbestimmung aus RPC
4. Firmwarestand erfassen
5. Hostname erfassen
6. Daten in `ip_state.json` aktualisieren

---

## 5. Ausgabeformate
Stage 2 schreibt pro Gerät eine Zeile, z. B.:

```text
S2PMG3 @ 192.168.1.51 - online (hostname=shelly-a23890, fw=1.4.99)
S1MINIPMG3 @ 192.168.1.54 - offline
I4G3 @ 192.168.1.30 - online (fw=1.7.1)
```

Farben werden in Stage 2 nicht verwendet.

---

## 6. Fehlerbilder & Lösungen

### Gerät offline
```text
S1MINIPMG3 @ 192.168.1.54 - offline
```
- IP falsch?
- Gerät nicht im Netzwerk?

### RPC-Fehler (HTTP 500 / 401 / 403)
- `Sys.GetConfig` nicht erreichbar
- Gerät hat Passwort aktiviert
- Lösung: Auth in `secrets.yaml` eintragen

### Ungültiges Modell
- RPC liefert unbekannten "model"
- Lösung: neue Modelle in Stage2 erweitern (Mapping aktualisieren)

---

## 7. Best Practices
- Vor Stage 3 immer Stage 2 laufen lassen
- Bei massiven IP-Änderungen: `--dry-run` zur Kontrolle
- `ip_state.json` nie direkt bearbeiten, außer zur Korrektur

---

## 8. Wichtige RPCs, die Stage 2 nutzt
- `Sys.GetStatus`
- `Sys.GetConfig`
- `Shelly.GetStatus`

---

Ende des Stage-2-Cheatsheets.