# Stage 2 – Adoption Runbook

**Runbook: Adoption von Shelly-Geräten (Stage 2)**  
**Version:** 1.0  
**Projekt:** Stagebox Provisioning Framework  
**Autor:** F. Forster / ChatGPT  
**Datum:** 2025-11-19

---

## 1. Zweck des Dokuments
Dieses Runbook beschreibt den strukturierten Prozess, um Shelly-Geräte, die:

- im WLAN hängen,
- aber noch nicht oder nicht mehr im IP-Pool sind,
- keinen Eintrag im ip_state.json besitzen,
- oder bereits einen Eintrag im ip_state.json haben,

neu oder erneut in das definierte Netz- und Namensschema aufzunehmen.

Es definiert den Standardablauf für den CLI-Betrieb (`shelly_stage2.py`) ohne Web-Interface.

---

## 2. Voraussetzungen
### 2.1 Software
- Raspberry Pi mit Debian/Ubuntu
- Python 3.11/3.12/3.13
- Stagebox-Projektstruktur:
  ```
  stagebox/
    data/
      ip_state.json
      shelly_model_map.yaml
    var/log/
    shelly_stage2.py
    config.yaml
    secrets.yaml
  ```

### 2.2 Konfiguration
Relevante Einstellungen in `config.yaml`: (Beispiel)

```
stage2:
  network:
    pool_start: 192.168.1.30
    pool_end:   192.168.1.99
    scan_cidr:  192.168.1.0/24
    dhcp_scan_start: 192.168.1.150
    dhcp_scan_end:   192.168.1.229
    scan_exclude_pool: true

  naming:
    enabled: true
  model_mapping_file: "data/shelly_model_map.yaml"

  logging:
    base_path: "var/log/stage2_session.log"

  inventory:
    enabled: false
```

### 2.3 Geräte
- Shelly Gen3 Geräte (Mini, 1PM, 2PM, I4, Plug)
- Geräte müssen im Heimnetz erreichbar sein, wenn dhcp_scan* definiert ist, müssen sie sich darin befinden. Dies ergibt den schnellsten scan

---

## 3. Definitionen
| Begriff | Bedeutung |
|--------|-----------|
| adoptieren | Ein Gerät, das im WLAN gefunden wird, aber keinen Pool-Eintrag hat, wird in den IP-Pool übernommen (Fix-IP + Hostname + JSON-Eintrag). |
| entlaufen | Gerät, das: DHCP verwendet, falsche IP, falschen Hostnamen oder keinen json-Eintrag hat. |
| Pool | Statisch definierter IP-Bereich. |
| scan | Vollständiger Netzwerk-Scan (CIDR, DHCP-Range) nach auffindbaren Shellys. |

---

## 4. Standardprozess – Adoption
### 4.1 Übersicht
1. Netzwerk scannen  
2. Geräte identifizieren  
3. Prüfen, ob sie im Pool sind  
4. Neue IP vergeben (falls nötig)  
5. Hostname setzen  
6. ip_state.json aktualisieren  
7. Logging schreiben  

Ausführung:
```
sudo python3 shelly_stage2.py --adopt
```

---

## 5. Ausführung
### 5.1 Trockendurchlauf
```
sudo python3 shelly_stage2.py --adopt --dry-run
```
Beispiel:
```
Adopt CIDR … scan=80, found=4, adopted=4, errors=0
```

### 5.2 Produktiver Lauf
```
sudo python3 shelly_stage2.py --adopt
```

---

## 6. Live-Output Interpretation
### 6.1 Erfolgreich adoptiert
```
S1MINIPMG3 @ 192.168.1.32 (shelly-ec8218) — OK
```

### 6.2 Fehlerfall
```
? @ 192.168.1.185 — Status: error (ip_assign_failed)
```

Ursachen:
- WLAN-Passwort fehlt
- Gerät rebootet während SetConfig
- Gerät im 90s-Recovery-Modus (I4)

---

## 7. Troubleshooting
### 7.1 I4 rebootet alle 90 Sekunden
Lösung:
1. Knopf 10 Sekunden gedrückt halten (nicht bis Fast-Blinking!)
2. Gerät rebootet sauber
3. Stage1 erneut durchführen

### 7.2 WiFi.SetConfig 500 Fehler
Shelly verlangt IMMER:
- SSID
- Password
- Gateway / Netmask / Nameserver / Static IP

Stage2 berücksichtigt dies bereits.

### 7.3 Gerät erhält neue IP, erscheint aber nicht online
Shelly benötigt:
- 2–5 Sekunden Reboot
- bis zu 10 Sekunden für WLAN

---

## 8. Dateien, die geändert werden
### Wird aktualisiert:
- `data/ip_state.json`
- `var/log/stage2_session.log`

---

## 9. Abschlusskriterien
Gerät gilt als adoptiert, wenn:
- IP im Pool
- Hostname gesetzt
- Modellname bekannt (model_map)
- JSON-Block vollständig
- Stage2 „OK“ liefert

---

## 10. Nächste Schritte
1. Stage3:
```
sudo python3 shelly_stage3.py
```
2. Stage4:
```
sudo python3 shelly_stage4.py
```
3. Label-CSV:
```
sudo python3 shelly_report.py --labels-mode band
```

---

## 11. Historie
| Version | Datum | Beschreibung |
|---------|--------|--------------|
| 1.0 | 2025-11-xx | Erstversion |

