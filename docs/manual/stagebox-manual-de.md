# Stagebox Web-UI Benutzerhandbuch

## Teil 1: Erste Schritte

Diese Anleitung führt Sie durch die Ersteinrichtung Ihrer Stagebox und das Erstellen Ihres ersten Gebäudeprojekts.
  



<img src="screenshots/01-stagebox-picture.png" width="700" alt="Produktbild">

### 1.1 Anschliessen der Stagebox

1. Verbinden Sie die Stagebox über ein Ethernet-Kabel mit Ihrem Netzwerk
2. Schliessen Sie das Netzteil an
3. Warten Sie etwa 60 Sekunden, bis das System gestartet ist
4. Das OLED-Display an der Vorderseite zeigt Verbindungsinformationen an

> **Hinweis:** Die Stagebox benötigt eine kabelgebundene Netzwerkverbindung. WiFi wird nur für die Provisionierung von Shelly-Geräten verwendet.

<div style="page-break-before: always;"></div>

### 1.2 Verwendung des OLED-Displays

Die Stagebox verfügt über ein integriertes OLED-Display, das automatisch durch mehrere Informationsbildschirme wechselt (alle 10 Sekunden).

**Bildschirm 1 - Splash (Hauptidentifikation):**

```
┌────────────────────────────┐
│                            │
│   ███ STAGEBOX ███         │
│                            │
│ ────────────────────────── │
│                            │
│   192.168.1.100            │
│                            │
│   A1:B2:C3                 │
│                            │
└────────────────────────────┘
```

Dieser Bildschirm zeigt:
- "STAGEBOX" Titel
- IP-Adresse für Web-Zugriff
- MAC-Suffix (letzte 6 Zeichen zur Identifikation)

**Bildschirm 2 - Gebäude-Info:**
- Aktuelle Stagebox-Version
- Aktiver Gebäudename

**Bildschirm 3 - Systemstatus:**
- CPU-Temperatur und -Auslastung
- NVMe-Temperatur
- RAM- und Festplattennutzung

**Bildschirm 4 - Netzwerk:**
- Ethernet-IP-Adresse
- WLAN-IP-Adresse (falls verbunden)
- Hostname

**Bildschirm 5 - Uhr:**
- Aktuelle Uhrzeit mit Sekunden
- Aktuelles Datum

<div style="page-break-before: always;"></div>

**OLED-Tastenfunktionen:**

Die Taste am Argon ONE Gehäuse steuert das Display:

| Druckdauer | Aktion |
|------------|--------|
| Kurzer Druck (<2s) | Zum nächsten Bildschirm wechseln |
| Langer Druck (2-10s) | Display ein-/ausschalten |
| Sehr langer Druck (10s+) | Admin-PIN auf `0000` zurücksetzen |

> **Tipp:** Verwenden Sie den Splash- oder Netzwerk-Bildschirm, um die IP-Adresse für den Zugriff auf die Web-UI zu finden.

<div style="page-break-before: always;"></div>

### 1.3 Zugriff auf die Web-Oberfläche

Finden Sie die IP-Adresse auf dem OLED-Display (Splash- oder Netzwerk-Bildschirm) und öffnen Sie dann einen Webbrowser:

```
http://<IP-ADRESSE>:5000
```

Zum Beispiel: `http://192.168.1.100:5000`

**Alternative mit Hostname:**

```
http://stagebox-XXXXXX.local:5000
```

Ersetzen Sie `XXXXXX` durch das MAC-Suffix, das auf dem OLED-Display angezeigt wird.

> **Hinweis:** Der `.local`-Hostname erfordert mDNS-Unterstützung (Bonjour). Falls er nicht funktioniert, verwenden Sie direkt die IP-Adresse.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Begrüssungsseite - Erster Zugriff">
<div style="page-break-before: always;"></div>

### 1.4 Als Admin anmelden

Administrative Funktionen sind durch eine PIN geschützt. Die Standard-PIN ist **0000**.

1. Klicken Sie auf **🔒 Admin** im Admin-Bereich
2. Geben Sie die PIN ein (Standard: `0000`)
3. Klicken Sie auf **Bestätigen**

Sie sind nun als Admin angemeldet (angezeigt als 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Admin-Anmeldung">

> **Sicherheitsempfehlung:** Ändern Sie die Standard-PIN sofort nach der ersten Anmeldung (siehe Abschnitt 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Ihr erstes Gebäude erstellen

Ein "Gebäude" in Stagebox repräsentiert ein Projekt oder einen Installationsort. Jedes Gebäude hat seine eigene Gerätedatenbank, IP-Pool und Konfiguration.

1. Stellen Sie sicher, dass Sie als Admin angemeldet sind (🔓 Admin sichtbar)
2. Klicken Sie auf **➕ Neues Gebäude**
3. Geben Sie einen Gebäudenamen ein (z.B. `kunde_haus`)
   - Verwenden Sie nur Kleinbuchstaben, Zahlen und Unterstriche
   - Leerzeichen und Sonderzeichen werden automatisch konvertiert
4. Klicken Sie auf **Erstellen**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="Neues Gebäude Dialog">

Das Gebäude wird erstellt und **öffnet sich automatisch** mit dem WiFi-Konfigurationsdialog.

---

> ⚠️ **KRITISCH: WiFi-Einstellungen korrekt konfigurieren!**
>
> Die WiFi-Einstellungen, die Sie hier eingeben, bestimmen, mit welchem Netzwerk sich Ihre Shelly-Geräte verbinden. **Falsche Einstellungen machen Geräte unerreichbar!**
>
> - Überprüfen Sie die SSID-Schreibweise (Gross-/Kleinschreibung beachten!)
> - Stellen Sie sicher, dass das Passwort korrekt ist
> - Stellen Sie sicher, dass die IP-Bereiche zu Ihrem tatsächlichen Netzwerk passen
>
> Geräte, die mit falschen WiFi-Zugangsdaten provisioniert wurden, müssen auf Werkseinstellungen zurückgesetzt und neu provisioniert werden.

<div style="page-break-before: always;"></div>

### 1.6 WiFi und IP-Bereiche konfigurieren

Nach dem Erstellen eines Gebäudes erscheint automatisch der **Gebäudeeinstellungen**-Dialog.

<img src="screenshots/07-building-settings.png" width="200" alt="Gebäudeeinstellungen">

#### WiFi-Konfiguration

Geben Sie die WiFi-Zugangsdaten ein, mit denen sich Shelly-Geräte verbinden sollen:

**Primäres WiFi (erforderlich):**
- SSID: Ihr Netzwerkname (z.B. `HeimNetzwerk`)
- Passwort: Ihr WiFi-Passwort

**Fallback-WiFi (optional):**
- Ein Backup-Netzwerk, falls das primäre nicht verfügbar ist

<img src="screenshots/08-wifi-settings.png" width="450" alt="WiFi-Einstellungen">

#### IP-Adressbereiche

Konfigurieren Sie den statischen IP-Pool für Shelly-Geräte:

**Shelly-Pool:**
- Von: Erste IP für Geräte (z.B. `192.168.1.50`)
- Bis: Letzte IP für Geräte (z.B. `192.168.1.99`)

**Gateway:**
- Normalerweise Ihre Router-IP (z.B. `192.168.1.1`)
- Leer lassen für automatische Erkennung (.1)

**DHCP-Scan-Bereich (optional):**
- Bereich, in dem neue Geräte nach Werksreset erscheinen
- Leer lassen, um das gesamte Subnetz zu scannen (langsamer)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="IP-Bereichseinstellungen">

> **Warnung:** Die IP-Bereiche müssen zu Ihrem tatsächlichen Netzwerk passen! Geräte sind unerreichbar, wenn sie mit falschem Subnetz konfiguriert werden.

5. Klicken Sie auf **💾 Speichern**

<div style="page-break-before: always;"></div>

### 1.7 Admin-PIN ändern

So ändern Sie Ihre Admin-PIN (Standard ist `0000`):

1. Klicken Sie auf **🔓 Admin** (muss angemeldet sein)
2. Klicken Sie auf **🔑 PIN ändern**
3. Geben Sie die neue PIN ein (mindestens 4 Ziffern)
4. Bestätigen Sie die neue PIN
5. Klicken Sie auf **Speichern**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="PIN ändern Dialog">

> **Wichtig:** Merken Sie sich diese PIN! Sie schützt alle administrativen Funktionen einschliesslich Gebäudelöschung und Systemeinstellungen.

### 1.8 Nächste Schritte

Ihre Stagebox ist nun bereit für die Geräteprovisionierung. Fahren Sie mit Teil 2 fort, um mehr zu erfahren über:
- Provisionierung neuer Shelly-Geräte (Stage 1-4)
- Geräteverwaltung
- Backups erstellen

---

<div style="page-break-before: always;"></div>

## Teil 2: Funktionsreferenz

### 2.1 Begrüssungsseite (Gebäudeauswahl)

Die Begrüssungsseite ist der Startpunkt nach dem Zugriff auf die Stagebox. Sie zeigt alle Gebäude und bietet systemweite Funktionen.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Begrüssungsseite Übersicht">

#### 2.1.1 Gebäudeliste

Der mittlere Bereich zeigt alle verfügbaren Gebäude als Karten an.

Jede Gebäudekarte zeigt:
- Gebäudename
- IP-Bereichszusammenfassung
- Geräteanzahl

**Aktionen (nur im Admin-Modus):**
- ✏️ Gebäude umbenennen
- 🗑️ Gebäude löschen

<img src="screenshots/21-building-cards.png" width="200" alt="Gebäudekarten">

**Gebäude auswählen:**
- Einfachklick zum Auswählen
- Doppelklick zum direkten Öffnen
- Nach Auswahl auf **Öffnen →** klicken

#### 2.1.2 System-Bereich

Links neben der Gebäudeliste:

| Button | Funktion | Admin erforderlich |
|--------|----------|-------------------|
| 💾 Backup auf USB | Backup aller Gebäude auf USB-Stick erstellen | Nein |
| 🔄 Neustart | Stagebox neu starten | Nein |
| ⏻ Herunterfahren | Stagebox sicher herunterfahren | Nein |

> **Wichtig:** Verwenden Sie immer **Herunterfahren** bevor Sie die Stromversorgung trennen, um Datenbeschädigung zu vermeiden.

#### 2.1.3 Admin-Bereich

Administrative Funktionen (erfordert Admin-PIN):

| Button | Funktion |
|--------|----------|
| 🔒/🔓 Admin | Anmelden/Abmelden |
| ➕ Neues Gebäude | Neues Gebäude erstellen |
| 📤 Alle Gebäude exportieren | ZIP aller Gebäude herunterladen |
| 📥 Gebäude importieren | Aus ZIP-Datei importieren |
| 📜 Shelly Script Pool | Gemeinsame Scripts verwalten |
| 📂 Von USB wiederherstellen | Gebäude aus USB-Backup wiederherstellen |
| 🔌 USB-Stick formatieren | USB für Backups vorbereiten |
| 🔑 PIN ändern | Admin-PIN ändern |
| 📦 Stagebox Update | Nach Software-Updates suchen |
| 🖥️ System Updates | Nach OS-Updates suchen |
| 🌐 Sprache | Oberflächensprache ändern |
| 🏢 Installateur-Profil | Firmeninformationen für Berichte konfigurieren |


#### 2.1.4 USB-Backup

**Backup erstellen:**

1. USB-Stick einstecken (beliebiges Format)
2. Falls nicht für Stagebox formatiert: Klicken Sie auf **🔌 USB-Stick formatieren** (Admin)
3. Klicken Sie auf **💾 Backup auf USB**
4. Warten Sie auf die Abschlussmeldung
5. USB-Stick kann nun sicher entfernt werden

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="USB-Format Dialog">

**Von USB wiederherstellen:**

1. USB-Stick mit Backups einstecken
2. Klicken Sie auf **📂 Von USB wiederherstellen** (Admin)
3. Wählen Sie ein Backup aus der Liste
4. Wählen Sie die wiederherzustellenden Gebäude
5. Klicken Sie auf **Ausgewählte wiederherstellen**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="USB-Wiederherstellung Dialog">

#### 2.1.5 Gebäude exportieren/importieren

**Export:**
1. Klicken Sie auf **📤 Alle Gebäude exportieren** (Admin)
2. Eine ZIP-Datei mit allen Gebäudedaten wird heruntergeladen

**Import:**
1. Klicken Sie auf **📥 Gebäude importieren** (Admin)
2. Ziehen Sie eine ZIP-Datei per Drag & Drop oder klicken Sie zum Auswählen
3. Wählen Sie, welche Gebäude importiert werden sollen
4. Wählen Sie die Aktion für bestehende Gebäude (überspringen/überschreiben)
5. Klicken Sie auf **Ausgewählte importieren**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Gebäude importieren Dialog">

<div style="page-break-before: always;"></div>

### 2.2 Gebäudeseite

Die Gebäudeseite ist der Hauptarbeitsbereich für die Provisionierung und Verwaltung von Geräten in einem bestimmten Gebäude.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Gebäudeseite Übersicht">

#### Layout:
- **Linke Seitenleiste:** Provisionierungsstufen, Filter, Aktionen, Einstellungen
- **Mittlerer Bereich:** Geräteliste
- **Rechte Seitenleiste:** Stage-Panels oder Gerätedetails, Script-, KVS-, Webhook- und OTA-Tabs

### 2.3 Linke Seitenleiste

#### 2.3.1 Gebäude-Header

Zeigt den aktuellen Gebäudenamen. Klicken Sie darauf, um zur Begrüssungsseite zurückzukehren.
<div style="page-break-before: always;"></div>

#### 2.3.2 Provisionierungsstufen

Die 4-stufige Provisionierungs-Pipeline:

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Provisionierungsstufen">

**S1 - AP-Provisionierung:**
- Sucht nach Shelly-Geräten im AP-Modus (Access Point)
- Konfiguriert WiFi-Zugangsdaten
- Deaktiviert Cloud, BLE und AP-Modus

**S2 - Adopt:**
- Scannt Netzwerk nach neuen Geräten (DHCP-Bereich)
- Weist statische IPs aus dem Pool zu
- Registriert Geräte in der Datenbank

**S3 - OTA & Namen:**
- Aktualisiert Firmware auf neueste Version
- Synchronisiert Friendly Names zu Geräten

**S4 - Konfigurieren:**
- Wendet Geräteprofile an
- Konfiguriert Eingänge, Schalter, Rollläden usw.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1: AP-Provisionierung

1. Klicken Sie auf **S1** Button
2. Der Stagebox WiFi-Adapter sucht nach Shelly APs
3. Gefundene Geräte werden automatisch konfiguriert, Gerätezähler zählt hoch
4. Klicken Sie auf **⏹ Stop** wenn fertig

<img src="screenshots/32-stage1-panel.png" width="450" alt="Stage 1 Panel">

> **Tipp:** Versetzen Sie Shelly-Geräte in den AP-Modus, indem Sie die Taste 10+ Sekunden gedrückt halten oder einen Werksreset durchführen.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2: Adopt

1. Klicken Sie auf **S2** Button
2. Klicken Sie auf **Netzwerk scannen**
3. Neue Geräte erscheinen in der Liste
4. Wählen Sie Geräte zum Adoptieren oder klicken Sie auf **Alle adoptieren**
5. Geräte erhalten statische IPs und werden registriert

<img src="screenshots/33-stage2-panel.png" width="300" alt="Stage 2 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3: OTA & Namen

1. Klicken Sie auf **S3** Button
2. Geräte in Stage 2 werden aufgelistet
3. Klicken Sie auf **Stage 3 ausführen** um:
   - Firmware zu aktualisieren (falls neuer verfügbar)
   - Friendly Names von Datenbank zu Geräten zu synchronisieren

<img src="screenshots/34-stage3-panel.png" width="300" alt="Stage 3 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4: Konfigurieren

1. Klicken Sie auf **S4** Button
2. Geräte in Stage 3 werden aufgelistet
3. Klicken Sie auf **Stage 4 ausführen** um Profile anzuwenden:
   - Schaltereinstellungen (Anfangszustand, Auto-Aus)
   - Rollladeneinstellungen (Richtung tauschen, Limits)
   - Eingangskonfigurationen
   - Benutzerdefinierte Aktionen

<img src="screenshots/35-stage4-panel.png" width="300" alt="Stage 4 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filter

Filtern Sie die Geräteliste nach verschiedenen Kriterien:

| Filter | Beschreibung |
|--------|--------------|
| Stage | Geräte in bestimmter Provisionierungsstufe anzeigen |
| Raum | Geräte in einem bestimmten Raum anzeigen |
| Modell | Bestimmte Gerätetypen anzeigen |
| Status | Online/Offline Geräte |

<img src="screenshots/36-filter-panel.png" width="200" alt="Filter Panel">

#### 2.3.8 Aktionen

Massenoperationen auf ausgewählten Geräten:

| Aktion | Beschreibung |
|--------|--------------|
| 🔄 Aktualisieren | Gerätestatus aktualisieren |
| 📋 Kopieren | Geräteinfo in Zwischenablage kopieren |
| 📤 CSV exportieren | Ausgewählte Geräte exportieren |
| 🗑️ Entfernen | Aus Datenbank entfernen (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Geräteliste

Der mittlere Bereich zeigt alle Geräte im aktuellen Gebäude.

<img src="screenshots/40-device-list.png" width="500" alt="Geräteliste">

#### Spalten:

| Spalte | Beschreibung |
|--------|--------------|
| ☑️ | Auswahlkästchen |
| Status | Online (🟢) / Offline (🔴) |
| Name | Geräte-Friendly-Name |
| Raum | Zugewiesener Raum |
| Ort | Position im Raum |
| Modell | Gerätetyp |
| IP | Aktuelle IP-Adresse |
| Stage | Aktuelle Provisionierungsstufe (S1-S4) |

#### Auswahl:
- Kontrollkästchen klicken, um einzelne Geräte auszuwählen
- Header-Kontrollkästchen klicken, um alle sichtbaren auszuwählen
- Umschalt+Klick für Bereichsauswahl

#### Sortierung:
- Spaltenüberschrift klicken zum Sortieren
- Erneut klicken für umgekehrte Reihenfolge

<div style="page-break-before: always;"></div>

### 2.5 Rechte Seitenleiste (Gerätedetails)

Wenn ein Gerät ausgewählt ist, zeigt die rechte Seitenleiste detaillierte Informationen und Aktionen.

#### 2.5.1 Geräte-Info Tab

Grundlegende Geräteinformationen:

| Feld | Beschreibung |
|------|--------------|
| Name | Bearbeitbarer Friendly Name |
| Raum | Raumzuweisung (bearbeitbar) |
| Ort | Position im Raum (bearbeitbar) |
| MAC | Hardware-Adresse |
| IP | Netzwerkadresse |
| Modell | Hardware-Modell |
| Firmware | Aktuelle Version |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Geräte-Info Tab">

<div style="page-break-before: always;"></div>

#### 2.5.2 Scripts Tab

Scripts auf dem ausgewählten Gerät verwalten:

- Installierte Scripts anzeigen
- Scripts starten/stoppen
- Scripts entfernen
- Neue Scripts deployen

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Geräte-Scripts Tab">

#### 2.5.3 KVS Tab

Key-Value Store Einträge anzeigen und bearbeiten:

- Systemwerte (nur lesen)
- Benutzerwerte (bearbeitbar)
- Neue Einträge hinzufügen
- Einträge löschen

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Geräte-KVS Tab">
<div style="page-break-before: always;"></div>

#### 2.5.4 Webhooks Tab

Geräte-Webhooks konfigurieren:

- Vorhandene Webhooks anzeigen
- Neue Webhooks hinzufügen
- URLs und Bedingungen bearbeiten
- Webhooks löschen

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Geräte-Webhooks Tab">

#### 2.5.5 Zeitpläne Tab

Geplante Aufgaben verwalten:

- Vorhandene Zeitpläne anzeigen
- Zeitbasierte Automatisierungen hinzufügen
- Zeitpläne aktivieren/deaktivieren
- Zeitpläne löschen

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Geräte-Zeitpläne Tab">

#### 2.5.6 Virtuelle Komponenten Tab

Virtuelle Komponenten auf Geräten konfigurieren:

- Virtuelle Schalter
- Virtuelle Sensoren
- Text-Komponenten
- Zahlen-Komponenten

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Geräte-Virtuals Tab">

#### 2.5.7 FW-Updates Tab

Geräte-Firmware verwalten:

- Aktuelle Version anzeigen
- Nach Updates suchen
- Firmware-Updates anwenden

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Geräte-FW-Updates Tab">
<div style="page-break-before: always;"></div>

### 2.6 Script-Verwaltung

#### 2.6.1 Script Pool (Admin)

Gemeinsame Scripts für Deployment verwalten:

1. Zur Begrüssungsseite gehen
2. Auf **📜 Shelly Script Pool** klicken (Admin)
3. JavaScript-Dateien (.js) hochladen
4. Unbenutzte Scripts löschen

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Script Pool Dialog">
<div style="page-break-before: always;"></div>

#### 2.6.2 Scripts deployen

1. Zielgerät(e) in Geräteliste auswählen
2. Zum **Scripts** Tab gehen
3. Quelle wählen: **Lokal** (Script Pool) oder **GitHub Library**
4. Ein Script auswählen
5. Optionen konfigurieren:
   - ☑️ Beim Start ausführen
   - ☑️ Nach Deploy starten
6. Auf **📤 Deploy** klicken

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Script Deploy Dialog">

<div style="page-break-before: always;"></div>

### 2.7 Experten-Einstellungen (Erweitert)

> ⚠️ **Warnung:** Die Experten-Einstellungen ermöglichen die direkte Konfiguration von Provisionierungsverhalten und Systemparametern. Falsche Änderungen können die Geräteprovisionierung beeinträchtigen. Mit Vorsicht verwenden!

Zugriff über **Experte** Bereich → **⚙️ Gebäudeeinstellungen** in der Gebäudeseiten-Seitenleiste.

Der Gebäudeeinstellungen-Dialog bietet eine Tab-Oberfläche für die Konfiguration erweiterter Optionen.

---

#### 2.7.1 Provisionierung Tab

Steuert das Verhalten der Stage 1 (AP-Modus) Provisionierung.

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Experte Provisionierung Tab">

| Einstellung | Beschreibung | Standard |
|-------------|--------------|----------|
| **Loop-Modus** | Kontinuierlich nach neuen Geräten suchen. Wenn aktiviert, sucht Stage 1 nach jeder erfolgreichen Provisionierung weiter nach neuen Shelly APs. Deaktivieren für Einzelgerät-Provisionierung. | ☑️ An |
| **AP nach Provisionierung deaktivieren** | WiFi Access Point des Geräts nach Verbindung mit Ihrem Netzwerk ausschalten. Empfohlen für Sicherheit. | ☑️ An |
| **Bluetooth deaktivieren** | Bluetooth auf provisionierten Geräten ausschalten. Spart Strom und reduziert Angriffsfläche. | ☑️ An |
| **Cloud deaktivieren** | Shelly Cloud-Verbindung deaktivieren. Geräte sind nur lokal erreichbar. | ☑️ An |
| **MQTT deaktivieren** | MQTT-Protokoll auf Geräten ausschalten. Aktivieren wenn Sie ein Hausautomationssystem mit MQTT verwenden. | ☑️ An |

---

#### 2.7.2 OTA & Namen Tab

Firmware-Update-Verhalten und Friendly-Name-Behandlung während Stage 3 konfigurieren.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Experte OTA Tab">

**Firmware-Updates (OTA):**

| Einstellung | Beschreibung | Standard |
|-------------|--------------|----------|
| **OTA-Updates aktivieren** | Während Stage 3 nach Firmware-Updates suchen und optional installieren. | ☑️ An |
| **Update-Modus** | `Nur prüfen`: Verfügbare Updates melden ohne zu installieren. `Prüfen & Aktualisieren`: Verfügbare Updates automatisch installieren. | Nur prüfen |
| **Timeout (Sekunden)** | Maximale Wartezeit für OTA-Operationen. Bei langsamen Netzwerken erhöhen. | 20 |

**Friendly Names:**

| Einstellung | Beschreibung | Standard |
|-------------|--------------|----------|
| **Friendly Names aktivieren** | Raum-/Ortsnamen während Stage 3 auf Geräte anwenden. Namen werden in der Gerätekonfiguration gespeichert. | ☑️ An |
| **Fehlende Namen ergänzen** | Automatisch Namen für Geräte ohne Zuweisung generieren. Verwendet das Muster `<Modell>_<MAC-Suffix>`. | ☐ Aus |

<div style="page-break-before: always;"></div>

#### 2.7.3 Export Tab

CSV-Export-Einstellungen für Gerätelabels und Berichte konfigurieren.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Experte Export Tab">

**CSV-Trennzeichen:**

Spaltentrennzeichen für exportierte CSV-Dateien wählen:
- **Semikolon (;)** - Standard, funktioniert mit europäischen Excel-Versionen
- **Komma (,)** - Standard CSV-Format
- **Tab** - Für Tab-getrennte Werte

**Standard-Spalten:**

Wählen Sie, welche Spalten in exportierten CSV-Dateien erscheinen. Verfügbare Spalten:

| Spalte | Beschreibung |
|--------|--------------|
| `id` | Geräte-MAC-Adresse (eindeutige Kennung) |
| `ip` | Aktuelle IP-Adresse |
| `hostname` | Geräte-Hostname |
| `fw` | Firmware-Version |
| `model` | Friendly Modellname |
| `hw_model` | Hardware-Modell-ID |
| `friendly_name` | Zugewiesener Gerätename |
| `room` | Raumzuweisung |
| `location` | Ort im Raum |
| `assigned_at` | Wann das Gerät provisioniert wurde |
| `last_seen` | Letzter Kommunikationszeitstempel |
| `stage3_friendly_status` | Namenszuweisungsstatus |
| `stage3_ota_status` | Firmware-Update-Status |
| `stage4_status_result` | Konfigurationsstufen-Ergebnis |

<div style="page-break-before: always;"></div>

#### 2.7.4 Model Map Tab

Benutzerdefinierte Anzeigenamen für Shelly Hardware-Modell-IDs definieren.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Experte Model Map Tab">

Die Model Map übersetzt interne Hardware-Kennungen (z.B. `SNSW-001X16EU`) in lesbare Namen (z.B. `Shelly Plus 1`).

**Verwendung:**
1. Die **Hardware-ID** exakt wie vom Gerät gemeldet eingeben
2. Ihren bevorzugten **Anzeigenamen** eingeben
3. **+ Modell hinzufügen** klicken für weitere Einträge
4. **🗑️** klicken um einen Eintrag zu entfernen

> **Tipp:** Prüfen Sie die Web-Oberfläche des Geräts oder die API-Antwort, um die exakte Hardware-ID-Zeichenkette zu finden.

<div style="page-break-before: always;"></div>

#### 2.7.5 Erweitert Tab (YAML-Editor)

Direkte Bearbeitung von Konfigurationsdateien für erweiterte Szenarien.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Experte Erweitert Tab">

**Verfügbare Dateien:**

| Datei | Beschreibung |
|-------|--------------|
| `config.yaml` | Hauptgebäudekonfiguration (IP-Bereiche, Gerätedatenbank, Provisionierungseinstellungen) |
| `profiles/*.yaml` | Gerätekonfigurationsprofile für Stage 4 |

**Funktionen:**
- Syntaxvalidierung (grüner/roter Indikator)
- Datei aus Dropdown auswählen
- Inhalt direkt bearbeiten
- Alle Änderungen werden vor dem Speichern automatisch gesichert

**Validierungsindikator:**
- 🟢 Grün: Gültige YAML-Syntax
- 🔴 Rot: Syntaxfehler (Hover für Details)

> **Empfehlung:** Verwenden Sie die anderen Tabs für normale Konfiguration. Verwenden Sie den YAML-Editor nur, wenn Sie Einstellungen ändern müssen, die nicht in der UI verfügbar sind, oder zur Fehlerbehebung.

<div style="page-break-before: always;"></div>

### 2.8 Systemwartung

#### 2.8.1 Stagebox Updates

Nach Stagebox Software-Updates suchen und installieren:

1. Zur Begrüssungsseite gehen
2. Auf **📦 Stagebox Update** klicken (Admin)
3. Aktuelle und verfügbare Versionen werden angezeigt
4. Auf **⬇️ Update installieren** klicken falls verfügbar
5. Auf Installation und automatischen Neustart warten

<img src="screenshots/80-stagebox-update.png" width="450" alt="Stagebox Update Dialog">
<div style="page-break-before: always;"></div>

#### 2.8.2 System Updates

Nach Betriebssystem-Updates suchen und installieren:

1. Zur Begrüssungsseite gehen
2. Auf **🖥️ System Updates** klicken (Admin)
3. Sicherheits- und System-Updates werden aufgelistet
4. Auf **⬇️ Updates installieren** klicken
5. System startet möglicherweise neu falls erforderlich

<img src="screenshots/81-system-updates.png" width="450" alt="System Updates Dialog">

---

<div style="page-break-before: always;"></div>

### 2.9 Berichte & Dokumentation

Stagebox bietet umfassende Berichtsfunktionen für professionelle Installationsdokumentation. Berichte enthalten Geräteinventare, Konfigurationsdetails und können mit Installateur-Branding angepasst werden.

#### 2.9.1 Installateur-Profil

Das Installateur-Profil enthält Ihre Firmeninformationen, die auf allen generierten Berichten erscheinen. Dies ist eine globale Einstellung, die für alle Gebäude gilt.

**Zugriff auf das Installateur-Profil:**

1. Zur Begrüssungsseite gehen
2. Auf **🏢 Installateur-Profil** klicken (Admin erforderlich)

**Verfügbare Felder:**

| Feld | Beschreibung |
|------|--------------|
| Firmenname | Ihr Firmen- oder Geschäftsname |
| Adresse | Strassenadresse (mehrzeilig möglich) |
| Telefon | Kontakttelefonnummer |
| E-Mail | Kontakt-E-Mail-Adresse |
| Website | Firmenwebsite-URL |
| Logo | Firmenlogo-Bild (PNG, JPG, max 2MB) |

**Logo-Richtlinien:**
- Empfohlene Grösse: 400×200 Pixel oder ähnliches Seitenverhältnis
- Formate: PNG (transparenter Hintergrund empfohlen) oder JPG
- Maximale Dateigrösse: 2MB
- Das Logo erscheint im Header von PDF-Berichten

> **Tipp:** Vervollständigen Sie das Installateur-Profil bevor Sie Ihren ersten Bericht erstellen, um professionell aussehende Dokumentation sicherzustellen.

<img src="screenshots/90-installer-profile.png" width="450" alt="Installateur-Profil Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.2 Gebäudeprofil (Objektinformationen)

Jedes Gebäude kann sein eigenes Profil mit kunden- und projektspezifischen Informationen haben. Diese Daten erscheinen in Berichten, die für dieses Gebäude generiert werden.

**Zugriff auf Gebäudeprofil:**

1. Gebäudeseite öffnen
2. Zum **Experte** Bereich in der Seitenleiste gehen
3. Auf **⚙️ Gebäudeeinstellungen** klicken
4. **Objekt** Tab auswählen

**Verfügbare Felder:**

| Feld | Beschreibung |
|------|--------------|
| Objektname | Projekt- oder Immobilienname (z.B. "Villa Müller") |
| Kundenname | Name des Kunden |
| Adresse | Immobilienadresse (mehrzeilig möglich) |
| Kontakttelefon | Telefonnummer des Kunden |
| Kontakt-E-Mail | E-Mail-Adresse des Kunden |
| Notizen | Zusätzliche Notizen (erscheinen in Berichten) |

> **Hinweis:** Der Objektname wird als Berichtstitel verwendet. Falls nicht gesetzt, wird stattdessen der Gebäudename verwendet.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Gebäudeprofil Tab">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Ein Snapshot erfasst den vollständigen Zustand aller Geräte in einem Gebäude zu einem bestimmten Zeitpunkt. Snapshots werden als ZIP-Bundles gespeichert, die Gerätedaten und Konfigurationsdateien enthalten.

**Snapshot erstellen:**

1. Gebäudeseite öffnen
2. Zum **Audit** Bereich in der Seitenleiste gehen
3. Auf **📸 Snapshots** klicken
4. Auf Abschluss des Scans warten

**Snapshot-Verwaltung:**

| Aktion | Beschreibung |
|--------|--------------|
| 📥 Download | Snapshot-ZIP-Bundle herunterladen |
| 🗑️ Löschen | Snapshot entfernen |

**Snapshot-ZIP-Inhalt:**

Jeder Snapshot wird als ZIP-Datei mit folgendem Inhalt gespeichert:

| Datei | Beschreibung |
|-------|--------------|
| `snapshot.json` | Vollständige Gerätescan-Daten (IP, MAC, Config, Status) |
| `installer_profile.json` | Installateur-Firmeninformationen |
| `installer_logo.png` | Firmenlogo (falls konfiguriert) |
| `ip_state.json` | Gerätedatenbank mit Raum-/Ortzuweisungen |
| `building_profile.json` | Objekt-/Kundeninformationen |
| `config.yaml` | Gebäudekonfiguration |
| `shelly_model_map.yaml` | Benutzerdefinierte Modellnamen-Zuordnungen (falls konfiguriert) |
| `scripts/*.js` | Deployete Scripts (falls vorhanden) |

> **Tipp:** Snapshots sind eigenständige Bundles, die mit externen Dokumentationswerkzeugen verwendet oder für zukünftige Referenz archiviert werden können.

**Automatische Bereinigung:**

Stagebox behält automatisch nur die 5 neuesten Snapshots pro Gebäude, um Speicherplatz zu sparen.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Snapshots Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.4 Berichtgenerator

Professionelle Installationsberichte im PDF- oder Excel-Format generieren.

**Bericht erstellen:**

1. Gebäudeseite öffnen
2. Zum **Audit** Bereich in der Seitenleiste gehen
3. Auf **📊 Berichtgenerator** klicken
4. Berichtsoptionen konfigurieren:
   - **Snapshot**: Neuen erstellen oder vorhandenen auswählen
   - **Sprache**: Berichtssprache (DE, EN, FR, IT, NL)
   - **Format**: PDF oder Excel (XLSX)
5. Auf **Generieren** klicken

<img src="screenshots/93-report-generator.png" width="450" alt="Berichtgenerator Dialog">

**PDF-Berichtsinhalt:**

Der PDF-Bericht enthält:
- **Header**: Firmenlogo, Berichtstitel, Erstellungsdatum
- **Objektinformationen**: Kundenname, Adresse, Kontaktdaten
- **Zusammenfassung**: Gesamtgeräte, Räume und Gerätetypen
- **Gerätetabelle**: Vollständiges Inventar mit QR-Codes

**Gerätetabellen-Spalten:**

| Spalte | Beschreibung |
|--------|--------------|
| QR | QR-Code verlinkt zur Geräte-Web-Oberfläche |
| Raum | Zugewiesener Raum |
| Ort | Position im Raum |
| Name | Geräte-Friendly-Name |
| Modell | Gerätetyp |
| IP | Netzwerkadresse |
| FW | Firmware-Version |
| MAC | Letzte 6 Zeichen der MAC-Adresse |
| SWTAK | Feature-Flags (siehe unten) |

**Feature-Flags (SWTAK):**

Jedes Gerät zeigt, welche Features konfiguriert sind:

| Flag | Bedeutung | Quelle |
|------|-----------|--------|
| **S** | Scripts | Gerät hat Scripts installiert |
| **W** | Webhooks | Gerät hat Webhooks konfiguriert |
| **T** | Timer | Auto-On oder Auto-Off Timer aktiv |
| **A** | Zeitpläne | Geplante Automatisierungen konfiguriert |
| **K** | KVS | Key-Value Store Einträge vorhanden |

Aktive Flags sind hervorgehoben, inaktive Flags sind ausgegraut.

**Excel-Bericht:**

Der Excel-Export enthält die gleichen Informationen wie das PDF im Tabellenformat:
- Einzelnes Arbeitsblatt mit allen Geräten
- Header mit Bericht-Metadaten
- Legende erklärt die SWTAK-Flags
- Spalten optimiert für Filterung und Sortierung

> **Tipp:** Verwenden Sie das Excel-Format, wenn Sie die Daten weiterverarbeiten oder benutzerdefinierte Dokumentation erstellen müssen.

<div style="page-break-before: always;"></div>

#### 2.9.5 Konfigurations-Audit

Die Audit-Funktion vergleicht den aktuellen Live-Zustand aller Geräte mit einem Referenz-Snapshot, um Konfigurationsänderungen, neue Geräte oder Offline-Geräte zu erkennen.

**Audit ausführen:**

1. Gebäudeseite öffnen
2. Zum **Audit** Bereich in der Seitenleiste gehen
3. Auf **🔍 Audit ausführen** klicken
4. Einen Referenz-Snapshot aus dem Dropdown auswählen
5. Auf **🔍 Audit starten** klicken

<img src="screenshots/94-audit-setup.png" width="450" alt="Audit-Setup Dialog">

Das System führt einen frischen Scan aller Geräte durch und vergleicht sie mit dem ausgewählten Snapshot.

**Audit-Ergebnisse:**

| Status | Icon | Beschreibung |
|--------|------|--------------|
| OK | ✅ | Gerät unverändert seit Snapshot |
| Geändert | ⚠️ | Konfigurationsunterschiede erkannt |
| Offline | ❌ | Gerät war im Snapshot aber antwortet nicht |
| Neu | 🆕 | Gerät gefunden, das nicht im Snapshot war |

<img src="screenshots/95-audit-results.png" width="500" alt="Audit-Ergebnisse">

**Erkannte Änderungen:**

Das Audit erkennt und meldet:
- IP-Adressänderungen
- Gerätenamenänderungen
- Firmware-Updates
- Konfigurationsänderungen (Eingangstypen, Schaltereinstellungen, Rollladeneinstellungen)
- WiFi-Einstellungsänderungen
- Neue oder fehlende Geräte

**Anwendungsfälle:**

- **Nach-Installations-Verifizierung**: Bestätigen, dass alle Geräte wie dokumentiert konfiguriert sind
- **Wartungsprüfungen**: Unerwartete Änderungen seit dem letzten Besuch erkennen
- **Fehlerbehebung**: Identifizieren, welche Einstellungen geändert wurden
- **Übergabedokumentation**: Installation vor Übergabe gegen Spezifikation prüfen

> **Tipp:** Erstellen Sie einen Snapshot nach Abschluss einer Installation, um ihn als Referenz für zukünftige Audits zu verwenden.

<div style="page-break-before: always;"></div>

## Anhang

### A. Tastaturkürzel

| Kürzel | Aktion |
|--------|--------|
| `Escape` | Dialog/Modal schliessen |
| `Enter` | Dialog bestätigen |

### B. Status-Indikatoren

| Icon | Bedeutung |
|------|-----------|
| 🟢 (grün) | Gerät online |
| 🔴 (rot) | Gerät offline |
| S1-S4 | Aktuelle Provisionierungsstufe |
| ⚡ | Firmware-Update verfügbar |

### C. Fehlerbehebung

**Web-UI nicht erreichbar:**
- Ethernet-Verbindung überprüfen
- Prüfen ob Stagebox IP hat (Router DHCP-Liste oder OLED-Display)
- IP-Adresse direkt statt .local versuchen

**Admin-PIN vergessen:**
- OLED-Taste **10+ Sekunden** gedrückt halten
- Display zeigt "PIN RESET" und "PIN = 0000"
- PIN ist nun auf Standard `0000` zurückgesetzt
- Mit `0000` anmelden und PIN sofort ändern

**Geräte nicht gefunden in Stage 1:**
- Sicherstellen, dass Gerät im AP-Modus ist (LED blinkt)
- Stagebox näher zum Gerät bewegen
- WiFi-Adapter-Verbindung prüfen

**Geräte nicht gefunden in Stage 2:**
- DHCP-Bereichseinstellungen überprüfen
- Prüfen ob Gerät mit richtigem WiFi verbunden ist
- 30 Sekunden nach Stage 1 warten

**Stage 4 schlägt fehl:**
- Gerätekompatibilität prüfen
- Überprüfen ob Profil für Gerätetyp existiert
- Prüfen ob Gerät online ist

**USB-Backup-Fehler:**
- USB-Stick entfernen und wieder einstecken
- Falls Fehler bestehen bleibt, Seite neu laden (Ctrl+F5)
- Sicherstellen, dass USB-Stick für Stagebox formatiert ist (Admin → USB-Stick formatieren)

**Berichtgenerierung langsam:**
- Grosse Installationen (50+ Geräte) können 10-20 Sekunden dauern
- PDF-Generierung erstellt QR-Codes für jedes Gerät
- Excel-Format für schnellere Generierung ohne QR-Codes verwenden

---

*Stagebox Web-UI Benutzerhandbuch - Version 1.5*