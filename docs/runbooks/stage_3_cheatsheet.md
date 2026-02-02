# Stage 3 Cheatsheet
Kompakte Referenz für Betrieb, Troubleshooting und typische CLI-Aufrufe von **Stage 3**.

---

## 1. Wichtigste CLI-Befehle

### Standardlauf
```bash
sudo python3 shelly_stage3.py
```
- OTA-Check / Update gemäß config
- Friendly-Sync gemäß config
- ip_state.json wird geschrieben

### Dry-Run (keine Änderungen)
```bash
sudo python3 shelly_stage3.py --dry-run
```
- OTA nur prüfen
- Friendly nicht schreiben
- ip_state.json unverändert

### Nur bestimmte IPs
```bash
sudo python3 shelly_stage3.py --ip 192.168.1.30 192.168.1.31
```

### Nur Online-Geräte anzeigen
```bash
sudo python3 shelly_stage3.py --online
```

### Quiet-Mode (nur Summary)
```bash
sudo python3 shelly_stage3.py --quiet
```

---

## 2. Bedeutung der Farben

### OTA
- **Grün**: `up_to_date`, `skipped`
- **Gelb**: Update verfügbar oder angestoßen (`updateable` / `update_available`)
- **Rot**: offline, Fehler (`offline`, `error`, `check_failed`)

### Friendly
- `Friendly=ok (Name)` → synchron oder erfolgreich gesetzt
- `Friendly=no_value` → JSON enthält keinen Friendly-Name
- `Friendly=error (Name) | ERR=...` → Fehler beim Setzen

---

## 3. OTA-Modi

### `check_only`
- Nur prüfen, ob Updates verfügbar sind
- Tritt nie ein Update los

### `check_and_update`
- Prüft auf Updates
- Führt Update aus, sofern verfügbar (kein Dry-Run)

### Fehlerbilder
- `OTA=offline` → Gerät nicht erreichbar
- `OTA=updateable` → Update verfügbar
- `OTA=error` → RPC-Fehler, Firmwarefehler, Zeitüberschreitung

---

## 4. Friendly-Modi

### `backfill: true`
- Gerät hat Priorität
- JSON → Device **nur**, wenn Device keinen Namen hat

### `backfill: false`
- JSON ist Master
- Device-Name wird **immer** überschrieben

### Typische Friendly-States
- `ok` → Name korrekt gesetzt oder schon synchron
- `no_value` → JSON hat keinen Friendly-Name
- `error` → Setzen ist fehlgeschlagen, siehe `ERR=...`

---

## 5. Typische Fehler & Lösungen

### Fehler: `OTA=offline`
- Gerät ist nicht erreichbar (Netzwerk, Strom)
- Prüfen:
  - IP korrekt?
  - Gerät im Browser erreichbar?

### Fehler: `Friendly=error | ERR=friendly: HTTP 500`
- Häufig wegen JSON-Formatproblemen
- Lösung: kompakte JSON-Strings (Stage3 macht dies bereits)

### Fehler: `ERR=Sys.GetConfig failed` / `401` / `403`
- Auth auf dem Gerät aktiviert
- Stage3 benötigt dann Basic Auth → in secrets.yaml abbildbar

### Fehler: ip_state.json nicht schreibbar
- Rechte prüfen (`chmod`, Besitzer)
- Dateisystem voll oder read-only?

---

## 6. Best Practices

- Vor Massenläufen: immer `--dry-run`
- Wenn viele Geräte offline: zuerst Netz prüfen, dann OTA laufen lassen
- Vor produktiven Changes: einzelne IP gezielt testen
- Friendly Names primär im Web-UI enforce'n

---

## 7. Beispielausgaben

### OK:
```text
● S2PMG3 @ 192.168.1.35 - OTA=up_to_date | Friendly=ok (Wohnzimmer)
```

### Update verfügbar:
```text
● S1MINIPMG3 @ 192.168.1.78 - OTA=updateable | Friendly=no_value
```

### Offline:
```text
● S1MINIPMG3 @ 192.168.1.54 - OTA=offline
```

### Fehler mit Detail:
```text
● I4G3 @ 192.168.1.30 - OTA=up_to_date | Friendly=error (Name) | ERR=friendly: HTTP 500
```

---

## 8. Schnellreferenz: wichtigste RPCs von Stage 3

- `Shelly.GetStatus`
- `Sys.GetConfig`
- `Shelly.CheckForUpdate`
- `Shelly.Update`
- `Sys.SetConfig` (Friendly-Name setzen)

Stage3 nutzt ausschließlich offiziell dokumentierte RPC-Endpunkte.

---

Ende des Stage-3-Cheatsheets.