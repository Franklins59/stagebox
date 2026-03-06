# Stagebox Web-UI Benutzerhandbuch

> *Dieses Handbuch entspricht der Stagebox Pro Version 1.1.0*

## Teil 1: Erste Schritte

Diese Anleitung führt Sie durch die Ersteinrichtung Ihrer Stagebox und das Erstellen Ihres ersten Gebäudeprojekts.
  


<img src="screenshots/01-stagebox-picture.png" width="700" alt="Product Picture">

### 1.1 Stagebox anschliessen

1. Verbinden Sie die Stagebox über ein Ethernet-Kabel mit Ihrem Netzwerk
2. Schliessen Sie das Netzteil an
3. Warten Sie ca. 60 Sekunden, bis das System gestartet ist
4. Das OLED-Display an der Vorderseite zeigt die Verbindungsinformationen an

> **Hinweis:** Die Stagebox benötigt eine kabelgebundene Netzwerkverbindung. WLAN wird nur für die Provisionierung von Shelly-Geräten verwendet.

<div style="page-break-before: always;"></div>

### 1.2 OLED-Display verwenden

Die Stagebox verfügt über ein eingebautes OLED-Display, das automatisch zwischen mehreren Informationsbildschirmen wechselt (alle 10 Sekunden).

**Bildschirm 1 — Splash (Hauptidentifikation):**

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
- «STAGEBOX»-Titel
- IP-Adresse für den Webzugriff
- MAC-Suffix (letzte 6 Zeichen zur Identifikation)

**Bildschirm 2 — Gebäudeinfo:**
- Aktuelle Stagebox-Version
- Aktiver Gebäudename

**Bildschirm 3 — Systemstatus:**
- CPU-Temperatur und -Auslastung
- NVMe-Temperatur
- RAM- und Speichernutzung

**Bildschirm 4 — Netzwerk:**
- Ethernet-IP-Adresse
- WLAN-IP-Adresse (falls verbunden)
- Hostname

**Bildschirm 5 — Uhr:**
- Aktuelle Uhrzeit mit Sekunden
- Aktuelles Datum

<div style="page-break-before: always;"></div>

**OLED-Tastenfunktionen:**

Die Taste am Argon-ONE-Gehäuse steuert das Display:

| Druckdauer | Aktion |
|------------|--------|
| Kurzer Druck (<2s) | Zum nächsten Bildschirm wechseln |
| Langer Druck (2–10s) | Display ein-/ausschalten |
| Sehr langer Druck (10s+) | Admin-PIN auf `0000` zurücksetzen |

> **Tipp:** Verwenden Sie den Splash- oder Netzwerk-Bildschirm, um die IP-Adresse für den Zugriff auf die Web-UI zu finden.

<div style="page-break-before: always;"></div>

### 1.3 Zugriff auf die Weboberfläche

Finden Sie die IP-Adresse auf dem OLED-Display (Splash- oder Netzwerk-Bildschirm) und öffnen Sie einen Webbrowser:

```
http://<IP-ADRESSE>:5000
```

Zum Beispiel: `http://192.168.1.100:5000`

**Alternative über Hostname:**

```
http://stagebox-XXXXXX.local:5000
```

Ersetzen Sie `XXXXXX` durch das auf dem OLED-Display angezeigte MAC-Suffix.

> **Hinweis:** Der `.local`-Hostname erfordert mDNS-Unterstützung (Bonjour). Falls er nicht funktioniert, verwenden Sie die IP-Adresse direkt.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Greeting Page - First Access">
<div style="page-break-before: always;"></div>
### 1.4 Als Admin anmelden

Administrative Funktionen sind durch eine PIN geschützt. Die Standard-PIN ist **0000**.

1. Klicken Sie auf **🔒 Admin** im Admin-Bereich
2. Geben Sie die PIN ein (Standard: `0000`)
3. Klicken Sie auf **Bestätigen**

Sie sind jetzt als Admin angemeldet (angezeigt als 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Admin Login">

> **Sicherheitsempfehlung:** Ändern Sie die Standard-PIN sofort nach der ersten Anmeldung (siehe Abschnitt 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Erstes Gebäude erstellen

Ein «Gebäude» in der Stagebox repräsentiert ein Projekt oder eine Installationsstelle. Jedes Gebäude hat seine eigene Gerätedatenbank, IP-Pool und Konfiguration.

1. Stellen Sie sicher, dass Sie als Admin angemeldet sind (🔓 Admin sichtbar)
2. Klicken Sie auf **➕ Neues Gebäude**
3. Geben Sie einen Gebäudenamen ein (z.B. `kundenhaus`)
   - Verwenden Sie nur Kleinbuchstaben, Zahlen und Unterstriche
   - Leerzeichen und Sonderzeichen werden automatisch konvertiert
4. Klicken Sie auf **Erstellen**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="New Building Dialog">

Das Gebäude wird erstellt und **öffnet sich automatisch** mit dem WLAN-Konfigurationsdialog.

---

> ⚠️ **WICHTIG: WLAN-Einstellungen korrekt konfigurieren!**
>
> Die hier eingegebenen WLAN-Einstellungen bestimmen, mit welchem Netzwerk sich Ihre Shelly-Geräte verbinden. **Falsche Einstellungen machen Geräte unerreichbar!**
>
> - SSID-Schreibweise prüfen (Gross-/Kleinschreibung beachten!)
> - Passwort überprüfen
> - Sicherstellen, dass die IP-Bereiche zu Ihrem Netzwerk passen
>
> Geräte, die mit falschen WLAN-Zugangsdaten provisioniert wurden, müssen zurückgesetzt und neu provisioniert werden.

<div style="page-break-before: always;"></div>

### 1.6 WLAN und IP-Bereiche konfigurieren

Nach dem Erstellen eines Gebäudes erscheint automatisch der Dialog **Gebäudeeinstellungen**.

<img src="screenshots/07-building-settings.png" width="200" alt="Building Settings">

#### WLAN-Konfiguration

Geben Sie die WLAN-Zugangsdaten ein, mit denen sich die Shelly-Geräte verbinden sollen:

**Primäres WLAN (erforderlich):**
- SSID: Ihr Netzwerkname (z.B. `HomeNetwork`)
- Passwort: Ihr WLAN-Passwort

**Fallback-WLAN (optional):**
- Ein Backup-Netzwerk, falls das primäre nicht verfügbar ist

<img src="screenshots/08-wifi-settings.png" width="450" alt="WiFi Settings">

#### IP-Adressbereiche

Konfigurieren Sie den statischen IP-Pool für Shelly-Geräte:

**Shelly Pool:**
- Von: Erste IP für Geräte (z.B. `192.168.1.50`)
- Bis: Letzte IP für Geräte (z.B. `192.168.1.99`)

**Gateway:**
- Normalerweise Ihre Router-IP (z.B. `192.168.1.1`)
- Leer lassen für automatische Erkennung (.1)

**DHCP-Scan-Bereich (optional):**
- Bereich, in dem neue Geräte nach einem Werksreset erscheinen
- Leer lassen, um das gesamte Subnetz zu scannen (langsamer)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="IP Range Settings">

> **Warnung:** Die IP-Bereiche müssen zu Ihrem tatsächlichen Netzwerk passen! Geräte sind nicht erreichbar, wenn sie mit einem falschen Subnetz konfiguriert werden.

5. Klicken Sie auf **💾 Speichern**

<div style="page-break-before: always;"></div>

### 1.7 Admin-PIN ändern

So ändern Sie Ihre Admin-PIN (Standard ist `0000`):

1. Klicken Sie auf **🔓 Admin** (muss angemeldet sein)
2. Klicken Sie auf **🔑 PIN ändern**
3. Geben Sie die neue PIN ein (mindestens 4 Stellen)
4. Bestätigen Sie die neue PIN
5. Klicken Sie auf **Speichern**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="Change PIN Dialog">

> **Wichtig:** Merken Sie sich diese PIN! Sie schützt alle administrativen Funktionen, einschliesslich Gebäudelöschung und Systemeinstellungen.

### 1.8 Nächste Schritte

Ihre Stagebox ist jetzt bereit für die Geräte-Provisionierung. Fahren Sie mit Teil 2 fort, um mehr zu erfahren über:
- Provisionierung neuer Shelly-Geräte (Stage 1–4)
- Geräteverwaltung
- Backups erstellen

---

<div style="page-break-before: always;"></div>

## Teil 2: Funktionsreferenz

### 2.1 Begrüssungsseite (Gebäudeauswahl)

Die Begrüssungsseite ist der Startpunkt nach dem Zugriff auf die Stagebox. Sie zeigt alle Gebäude und bietet systemweite Funktionen.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Greeting Page Overview">

#### 2.1.1 Gebäudeliste

Der mittlere Bereich zeigt alle verfügbaren Gebäude als Karten an.

Jede Gebäudekarte zeigt:
- Gebäudename
- IP-Bereich-Zusammenfassung
- Geräteanzahl

**Aktionen (nur im Admin-Modus):**
- ✏️ Gebäude umbenennen
- 🗑️ Gebäude löschen

<img src="screenshots/21-building-cards.png" width="200" alt="Building Cards">

**Gebäude auswählen:**
- Einfachklick zum Auswählen
- Doppelklick zum direkten Öffnen
- Nach dem Auswählen auf **Öffnen →** klicken

#### 2.1.2 System-Bereich

Links neben der Gebäudeliste:

| Schaltfläche | Funktion | Admin erforderlich |
|--------------|----------|-------------------|
| 💾 Backup auf USB | Backup aller Gebäude auf USB-Stick erstellen | Nein |
| 🔄 Neustart | Stagebox neu starten | Nein |
| ⏻ Herunterfahren | Stagebox sicher herunterfahren | Nein |

> **Wichtig:** Verwenden Sie immer **Herunterfahren**, bevor Sie das Netzteil trennen, um Datenverlust zu vermeiden.

#### 2.1.3 Admin-Bereich

Administrative Funktionen (erfordert Admin-PIN):

| Schaltfläche | Funktion |
|--------------|----------|
| 🔒/🔓 Admin | Anmelden/Abmelden |
| ➕ Neues Gebäude | Neues Gebäude erstellen |
| 📤 Alle Gebäude exportieren | ZIP-Datei aller Gebäude herunterladen |
| 📥 Gebäude importieren | Aus ZIP-Datei importieren |
| 📜 Shelly Script Pool | Gemeinsame Skripte verwalten |
| 📂 Von USB wiederherstellen | Gebäude aus USB-Backup wiederherstellen |
| 🔌 USB-Stick formatieren | USB für Backups vorbereiten |
| 🔑 PIN ändern | Admin-PIN ändern |
| 📦 Stagebox Update | Auf Software-Updates prüfen |
| 🖥️ System-Updates | Auf OS-Updates prüfen |
| 🌐 Sprache | Sprache der Oberfläche ändern |
| 🏢 Installateur-Profil | Firmeninformationen für Berichte konfigurieren |


#### 2.1.4 USB-Backup

**Backup erstellen:**

1. USB-Stick einstecken (beliebiges Format)
2. Falls nicht für Stagebox formatiert: Klicken Sie auf **🔌 USB-Stick formatieren** (Admin)
3. Klicken Sie auf **💾 Backup auf USB**
4. Warten Sie auf die Abschlussmeldung
5. USB-Stick kann nun sicher entfernt werden

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="USB Format Dialog">

**Von USB wiederherstellen:**

1. USB-Stick mit Backups einstecken
2. Klicken Sie auf **📂 Von USB wiederherstellen** (Admin)
3. Wählen Sie ein Backup aus der Liste
4. Wählen Sie die wiederherzustellenden Gebäude
5. Klicken Sie auf **Ausgewählte wiederherstellen**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="USB Restore Dialog">

#### 2.1.5 Gebäude exportieren/importieren

**Export:**
1. Klicken Sie auf **📤 Alle Gebäude exportieren** (Admin)
2. Eine ZIP-Datei mit allen Gebäudedaten wird heruntergeladen

**Import:**
1. Klicken Sie auf **📥 Gebäude importieren** (Admin)
2. ZIP-Datei per Drag & Drop ablegen oder klicken zum Auswählen
3. Wählen Sie die zu importierenden Gebäude
4. Wählen Sie die Aktion für bestehende Gebäude (überspringen/überschreiben)
5. Klicken Sie auf **Ausgewählte importieren**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Import Buildings Dialog">

<div style="page-break-before: always;"></div>

### 2.2 Gebäudeseite

Die Gebäudeseite ist der Hauptarbeitsbereich für die Provisionierung und Verwaltung von Geräten in einem bestimmten Gebäude.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Building Page Overview">

#### Layout:
- **Linke Seitenleiste:** Provisionierungsstufen, Filter, Aktionen, Einstellungen
- **Mittlerer Bereich:** Geräteliste
- **Rechte Seitenleiste:** Stage-Panels oder Gerätedetails, Script-, KVS-, Webhook-, Zeitplan- und OTA-Tabs

### 2.3 Linke Seitenleiste

#### 2.3.1 Gebäude-Header

Zeigt den aktuellen Gebäudenamen. Klicken Sie darauf, um zur Begrüssungsseite zurückzukehren.
<div style="page-break-before: always;"></div>

#### 2.3.2 Provisionierungsstufen

Die 4-stufige Provisionierungs-Pipeline:

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Provisioning Stages">

**S1 — AP-Provisionierung:**
- Sucht nach Shelly-Geräten im AP-Modus (Access Point)
- Konfiguriert WLAN-Zugangsdaten
- Deaktiviert Cloud, BLE und AP-Modus

**S2 — Adopt:**
- Scannt das Netzwerk nach neuen Geräten (DHCP-Bereich)
- Weist statische IPs aus dem Pool zu
- Registriert Geräte in der Datenbank

**S3 — OTA & Namen:**
- Aktualisiert Firmware auf die neueste Version
- Synchronisiert Anzeigenamen auf Geräte

**S4 — Konfigurieren:**
- Wendet Geräteprofile an
- Konfiguriert Eingänge, Schalter, Rollläden usw.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1: AP-Provisionierung

1. Klicken Sie auf die Schaltfläche **S1**
2. Der Stagebox-WLAN-Adapter sucht nach Shelly-APs
3. Gefundene Geräte werden automatisch konfiguriert, der Gerätezähler zählt hoch
4. Klicken Sie auf **⏹ Stop**, wenn fertig

<img src="screenshots/32-stage1-panel.png" width="450" alt="Stage 1 Panel">

> **Tipp:** Versetzen Sie Shelly-Geräte in den AP-Modus, indem Sie die Taste 10+ Sekunden gedrückt halten oder einen Werksreset durchführen.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2: Adopt

1. Klicken Sie auf die Schaltfläche **S2**
2. Klicken Sie auf **Netzwerk scannen**
3. Neue Geräte erscheinen in der Liste
4. Wählen Sie Geräte zum Adoptieren oder klicken Sie auf **Alle adoptieren**
5. Geräte erhalten statische IPs und werden registriert

<img src="screenshots/33-stage2-panel.png" width="300" alt="Stage 2 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3: OTA & Namen

1. Klicken Sie auf die Schaltfläche **S3**
2. Geräte in Stage 2 werden aufgelistet
3. Klicken Sie auf **Stage 3 ausführen**, um:
   - Firmware zu aktualisieren (falls neuere verfügbar)
   - Anzeigenamen von der Datenbank auf Geräte zu synchronisieren

<img src="screenshots/34-stage3-panel.png" width="300" alt="Stage 3 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4: Konfigurieren

1. Klicken Sie auf die Schaltfläche **S4**
2. Geräte in Stage 3 werden aufgelistet
3. Klicken Sie auf **Stage 4 ausführen**, um Profile anzuwenden:
   - Schaltereinstellungen (Initialzustand, Auto-Off)
   - Rollladeneinstellungen (Richtung tauschen, Limits)
   - Eingangskonfigurationen
   - Benutzerdefinierte Aktionen

<img src="screenshots/35-stage4-panel.png" width="300" alt="Stage 4 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filter

Filtern Sie die Geräteliste nach verschiedenen Kriterien:

| Filter | Beschreibung |
|--------|-------------|
| Stage | Geräte in einer bestimmten Provisionierungsstufe anzeigen |
| Raum | Geräte in einem bestimmten Raum anzeigen |
| Modell | Bestimmte Gerätetypen anzeigen |
| Status | Online-/Offline-Geräte |

<img src="screenshots/36-filter-panel.png" width="200" alt="Filter Panel">

#### 2.3.8 Aktionen

Massenoperationen auf ausgewählten Geräten:

| Aktion | Beschreibung |
|--------|-------------|
| 🔄 Aktualisieren | Gerätestatus aktualisieren |
| 📋 Kopieren | Geräteinfo in Zwischenablage kopieren |
| 📤 CSV exportieren | Ausgewählte Geräte exportieren |
| 🗑️ Entfernen | Aus Datenbank entfernen (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Geräteliste

Der mittlere Bereich zeigt alle Geräte im aktuellen Gebäude.

<img src="screenshots/40-device-list.png" width="500" alt="Device List">

#### Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| ☑️ | Auswahl-Checkbox |
| Status | Online (🟢) / Offline (🔴) |
| Name | Anzeigename des Geräts |
| Raum | Zugewiesener Raum |
| Standort | Position innerhalb des Raums |
| Modell | Gerätetyp |
| IP | Aktuelle IP-Adresse |
| Stage | Aktuelle Provisionierungsstufe (S1–S4) |

#### Auswahl:
- Checkbox klicken, um einzelne Geräte auszuwählen
- Header-Checkbox klicken, um alle sichtbaren auszuwählen
- Shift+Klick für Bereichsauswahl

#### Sortierung:
- Spaltenüberschrift klicken zum Sortieren
- Erneut klicken für umgekehrte Reihenfolge

<div style="page-break-before: always;"></div>

### 2.5 Rechte Seitenleiste (Gerätedetails)

Wenn ein Gerät ausgewählt ist, zeigt die rechte Seitenleiste detaillierte Informationen und Aktionen.

#### 2.5.1 Geräteinfo-Tab

Grundlegende Geräteinformationen:

| Feld | Beschreibung |
|------|-------------|
| Name | Bearbeitbarer Anzeigename |
| Raum | Raumzuweisung (bearbeitbar) |
| Standort | Position innerhalb des Raums (bearbeitbar) |
| MAC | Hardware-Adresse |
| IP | Netzwerkadresse |
| Modell | Hardware-Modell |
| Firmware | Aktuelle Version |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Device Info Tab">

<div style="page-break-before: always;"></div>

#### 2.5.2 Scripts-Tab

Skripte auf dem ausgewählten Gerät verwalten:

- Installierte Skripte anzeigen
- Skripte starten/stoppen
- Skripte entfernen
- Neue Skripte bereitstellen

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Device Scripts Tab">

#### 2.5.3 KVS-Tab

Key-Value-Store-Einträge anzeigen und bearbeiten:

- Systemwerte (schreibgeschützt)
- Benutzerwerte (bearbeitbar)
- Neue Einträge hinzufügen
- Einträge löschen

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Device KVS Tab">
<div style="page-break-before: always;"></div>

#### 2.5.4 Webhooks-Tab

Geräte-Webhooks konfigurieren:

- Bestehende Webhooks anzeigen
- Neue Webhooks hinzufügen
- URLs und Bedingungen bearbeiten
- Webhooks löschen

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Device Webhooks Tab">
<div style="page-break-before: always;"></div>

#### 2.5.5 Zeitplan-Tab

Der Zeitplan-Tab ermöglicht das Erstellen, Verwalten und Bereitstellen von zeitbasierten Automatisierungen auf Shelly-Geräte. Zeitpläne werden als Vorlagen gespeichert und können gleichzeitig auf mehrere kompatible Geräte bereitgestellt werden.

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Device Schedules Tab">

**Tab-Übersicht:**

Der Zeitplan-Tab ist in drei Bereiche unterteilt:

1. **Vorlagenliste** — gespeicherte Zeitplanvorlagen mit Bearbeitungs-/Löschfunktionen
2. **Zielgeräte** — Checkbox-Liste zur Auswahl der Bereitstellungsziele
3. **Aktionsschaltflächen** — Bereitstellen, Status und Alle löschen

##### Zeitplan erstellen

1. Klicken Sie auf **+ Neu**, um den Zeitplan-Editor zu öffnen
2. Geben Sie einen **Namen** und eine optionale **Beschreibung** ein

<img src="screenshots/54a-schedule-editor-modal.png" width="500" alt="Schedule Editor Modal">

**Linke Spalte — Zeitsteuerung:**

Wählen Sie einen von vier Zeitsteuerungsmodi:

| Modus | Beschreibung |
|-------|-------------|
| 🕐 **Uhrzeit** | Bestimmte Tageszeit festlegen (Stunden und Minuten) |
| 🌅 **Sonnenaufgang** | Auslösung bei Sonnenaufgang, mit optionalem Offset |
| 🌇 **Sonnenuntergang** | Auslösung bei Sonnenuntergang, mit optionalem Offset |
| 📅 **Intervall** | Wiederholung in regelmässigen Abständen — wählen Sie aus Voreinstellungen (alle 5 Min., 15 Min., 30 Min., stündlich, alle 2 Stunden) oder geben Sie benutzerdefinierte Minuten-/Stundenwerte ein |

Unterhalb des Zeitsteuerungsmodus wählen Sie die **Wochentage** über Checkboxen (Mo–So).

Das **Zeitplan**-Feld zeigt den generierten Shelly-Cron-Ausdruck (schreibgeschützt). Darunter wird eine Vorschau der nächsten geplanten Ausführungszeiten angezeigt.

Die **Aktiviert**-Checkbox steuert, ob der Zeitplan nach der Bereitstellung aktiv ist.

**Rechte Spalte — Aktionen:**

3. Wählen Sie ein **Referenzgerät** aus dem Dropdown — Stagebox fragt dieses Gerät ab, um die verfügbaren Komponenten und Aktionen zu ermitteln (z.B. Switch, Cover, Light)
4. Fügen Sie eine oder mehrere **Aktionen** hinzu (bis zu 5 pro Zeitplan) über **+ Aktion hinzufügen**:
   - Die verfügbaren Methoden hängen von den Komponenten des Referenzgeräts ab
   - Beispiele: `Switch.Set` (ein/aus), `Cover.GoToPosition` (0–100), `Light.Set` (ein/aus/Helligkeit)
   - Entfernen Sie eine Aktion mit der **✕**-Schaltfläche

5. Klicken Sie auf **💾 Speichern**, um die Vorlage zu speichern, oder **Abbrechen** zum Verwerfen

> **Tipp:** Das Referenzgerät bestimmt, welche Aktionen verfügbar sind. Wählen Sie ein Gerät, das die Komponenten hat, die Sie steuern möchten.

##### Zeitplan bearbeiten

- Klicken Sie auf die **✏️ Bearbeiten**-Schaltfläche neben einer Vorlage oder **doppelklicken** Sie auf den Vorlagennamen
- Der Zeitplan-Editor öffnet sich vorausgefüllt mit den bestehenden Einstellungen
- Ändern Sie die Einstellungen und klicken Sie auf **💾 Speichern**

##### Zeitpläne bereitstellen

1. Wählen Sie eine Zeitplanvorlage aus der Liste
2. Markieren Sie die Zielgeräte im Bereich **Zielgeräte**
   - Verwenden Sie **Alle auswählen** / **Keine** für schnelle Auswahl
   - Inkompatible Geräte (fehlende erforderliche Komponenten) werden bei der Bereitstellung automatisch übersprungen
3. Klicken Sie auf **📤 Bereitstellen**
4. Die Ergebnisse werden pro Gerät mit Erfolgs-/Fehlerstatus angezeigt

> **Hinweis:** Vor der Bereitstellung prüft Stagebox jedes Zielgerät auf die erforderlichen Komponenten. Geräte, denen die notwendigen Komponenten fehlen (z.B. einen Cover-Zeitplan auf ein Nur-Switch-Gerät bereitstellen), werden mit einer Fehlermeldung übersprungen.

##### Zeitplan-Status prüfen

1. Zielgeräte auswählen
2. Klicken Sie auf **📋 Status**
3. Stagebox fragt jedes Gerät ab und zeigt die aktuell installierten Zeitpläne an, einschliesslich Timespec, Methode und Aktiviert/Deaktiviert-Status

##### Zeitpläne von Geräten löschen

1. Zielgeräte auswählen
2. Klicken Sie auf **🗑️ Alle löschen**
3. Alle Zeitpläne auf den ausgewählten Geräten werden entfernt

> **Warnung:** «Alle löschen» entfernt **alle** Zeitpläne von den ausgewählten Geräten, nicht nur die von Stagebox bereitgestellten.

<img src="screenshots/54b-schedule-tab-overview.png" width="300" alt="Schedule Tab Overview">
<div style="page-break-before: always;"></div>

#### 2.5.6 Virtuelle Komponenten-Tab

Virtuelle Komponenten auf Geräten konfigurieren:

- Virtuelle Schalter
- Virtuelle Sensoren
- Text-Komponenten
- Zahlen-Komponenten

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Device Virtuals Tab">

#### 2.5.7 FW-Updates-Tab

Geräte-Firmware verwalten:

- Aktuelle Version anzeigen
- Auf Updates prüfen
- Firmware-Updates anwenden

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Device FW-Updates Tab">
<div style="page-break-before: always;"></div>

### 2.6 Skriptverwaltung

#### 2.6.1 Script Pool (Admin)

Gemeinsame Skripte für die Bereitstellung verwalten:

1. Gehen Sie zur Begrüssungsseite
2. Klicken Sie auf **📜 Shelly Script Pool** (Admin)
3. JavaScript-Dateien (.js) hochladen
4. Nicht benötigte Skripte löschen

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Script Pool Dialog">
<div style="page-break-before: always;"></div>

#### 2.6.2 Skripte bereitstellen

1. Zielgerät(e) in der Geräteliste auswählen
2. Zum **Scripts**-Tab wechseln
3. Quelle auswählen: **Lokal** (Script Pool) oder **GitHub-Bibliothek**
4. Ein Skript auswählen
5. Optionen konfigurieren:
   - ☑️ Beim Start ausführen
   - ☑️ Nach Bereitstellung starten
6. Klicken Sie auf **📤 Bereitstellen**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Deploy Script Dialog">

<div style="page-break-before: always;"></div>

### 2.7 Experteneinstellungen (Erweitert)

> ⚠️ **Warnung:** Die Experteneinstellungen ermöglichen die direkte Konfiguration des Provisionierungsverhaltens und der Systemparameter. Falsche Änderungen können die Geräte-Provisionierung beeinträchtigen. Mit Vorsicht verwenden!

Zugriff über **Experten**-Bereich → **⚙️ Gebäudeeinstellungen** in der Seitenleiste der Gebäudeseite.

Der Dialog Gebäudeeinstellungen bietet eine Tab-basierte Oberfläche zur Konfiguration erweiterter Optionen.

---

#### 2.7.1 Provisionierungs-Tab

Steuert das Verhalten der Stage 1 (AP-Modus) Provisionierung.

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Expert Provisioning Tab">

| Einstellung | Beschreibung | Standard |
|-------------|-------------|----------|
| **Schleifen-Modus** | Kontinuierlich nach neuen Geräten suchen. Wenn aktiviert, sucht Stage 1 nach jeder erfolgreichen Provisionierung weiter nach neuen Shelly-APs. Deaktivieren für Einzelgerät-Provisionierung. | ☑️ An |
| **AP nach Provisionierung deaktivieren** | WLAN-Access-Point des Geräts ausschalten, nachdem es sich mit Ihrem Netzwerk verbunden hat. Aus Sicherheitsgründen empfohlen. | ☑️ An |
| **Bluetooth deaktivieren** | Bluetooth auf provisionierten Geräten ausschalten. Spart Strom und reduziert die Angriffsfläche. | ☑️ An |
| **Cloud deaktivieren** | Shelly-Cloud-Konnektivität deaktivieren. Geräte sind nur lokal erreichbar. | ☑️ An |
| **MQTT deaktivieren** | MQTT-Protokoll auf Geräten ausschalten. Aktivieren, wenn Sie ein Hausautomationssystem mit MQTT verwenden. | ☑️ An |

---

#### 2.7.2 OTA & Namen-Tab

Firmware-Update-Verhalten und Anzeigenamen-Behandlung während Stage 3 konfigurieren.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Expert OTA & Names Tab">

**Firmware-Updates (OTA):**

| Einstellung | Beschreibung | Standard |
|-------------|-------------|----------|
| **OTA-Updates aktivieren** | Während Stage 3 auf Firmware-Updates prüfen und optional installieren. | ☑️ An |
| **Update-Modus** | `Nur prüfen`: Verfügbare Updates melden, ohne sie zu installieren. `Prüfen & aktualisieren`: Verfügbare Updates automatisch installieren. | Nur prüfen |
| **Timeout (Sekunden)** | Maximale Wartezeit für OTA-Vorgänge. Bei langsamen Netzwerken erhöhen. | 20 |

**Anzeigenamen:**

| Einstellung | Beschreibung | Standard |
|-------------|-------------|----------|
| **Anzeigenamen aktivieren** | Raum-/Standortnamen während Stage 3 auf Geräte anwenden. Namen werden in der Gerätekonfiguration gespeichert. | ☑️ An |
| **Fehlende Namen ergänzen** | Automatisch Namen für Geräte generieren, die keinen zugewiesen haben. Verwendet das Muster `<Modell>_<MAC-Suffix>`. | ☐ Aus |

<div style="page-break-before: always;"></div>

#### 2.7.3 Export-Tab

CSV-Exporteinstellungen für Gerätelabels und Berichte konfigurieren.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Expert Export Tab">

**CSV-Trennzeichen:**

Wählen Sie das Spaltentrennzeichen für exportierte CSV-Dateien:
- **Semikolon (;)** — Standard, funktioniert mit europäischen Excel-Versionen
- **Komma (,)** — Standard-CSV-Format
- **Tab** — Für tabulatorgetrennte Werte

**Standardspalten:**

Wählen Sie, welche Spalten in exportierten CSV-Dateien erscheinen. Verfügbare Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| `id` | Geräte-MAC-Adresse (eindeutiger Bezeichner) |
| `ip` | Aktuelle IP-Adresse |
| `hostname` | Geräte-Hostname |
| `fw` | Firmware-Version |
| `model` | Anzeige-Modellname |
| `hw_model` | Hardware-Modell-ID |
| `friendly_name` | Zugewiesener Gerätename |
| `room` | Raumzuweisung |
| `location` | Standort innerhalb des Raums |
| `assigned_at` | Zeitpunkt der Provisionierung |
| `last_seen` | Letzter Kommunikationszeitpunkt |
| `stage3_friendly_status` | Namenzuweisungsstatus |
| `stage3_ota_status` | Firmware-Update-Status |
| `stage4_status_result` | Ergebnis der Konfigurationsstufe |

<div style="page-break-before: always;"></div>

#### 2.7.4 Modell-Map-Tab

Benutzerdefinierte Anzeigenamen für Shelly-Hardware-Modell-IDs definieren.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Expert Model Map Tab">

Die Modell-Map übersetzt interne Hardware-Bezeichner (z.B. `SNSW-001X16EU`) in lesbare Namen (z.B. `Shelly Plus 1`).

**Verwendung:**
1. Geben Sie die **Hardware-ID** genau so ein, wie sie vom Gerät gemeldet wird
2. Geben Sie Ihren bevorzugten **Anzeigenamen** ein
3. Klicken Sie auf **+ Modell hinzufügen**, um weitere Einträge hinzuzufügen
4. Klicken Sie auf **🗑️**, um einen Eintrag zu entfernen

> **Tipp:** Überprüfen Sie die Weboberfläche oder API-Antwort des Geräts, um die exakte Hardware-ID zu finden.

<div style="page-break-before: always;"></div>

#### 2.7.5 Erweitert-Tab (YAML-Editor)

Direkte Bearbeitung von Konfigurationsdateien für erweiterte Szenarien.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Expert Advanced Tab">

**Verfügbare Dateien:**

| Datei | Beschreibung |
|-------|-------------|
| `config.yaml` | Haupt-Gebäudekonfiguration (IP-Bereiche, Gerätedatenbank, Provisionierungseinstellungen) |
| `profiles/*.yaml` | Geräte-Konfigurationsprofile für Stage 4 |

**Funktionen:**
- Syntaxvalidierung (grüner/roter Indikator)
- Datei aus Dropdown auswählen
- Inhalt direkt bearbeiten
- Alle Änderungen werden vor dem Speichern automatisch gesichert

**Validierungsindikator:**
- 🟢 Grün: Gültige YAML-Syntax
- 🔴 Rot: Syntaxfehler (Details beim Hovern)

> **Empfehlung:** Verwenden Sie die anderen Tabs für die normale Konfiguration. Nutzen Sie den YAML-Editor nur, wenn Sie Einstellungen ändern müssen, die nicht in der UI verfügbar sind, oder zur Fehlerbehebung.

<div style="page-break-before: always;"></div>

### 2.8 Systemwartung

#### 2.8.1 Stagebox-Updates

Stagebox-Software-Updates prüfen und installieren:

1. Gehen Sie zur Begrüssungsseite
2. Klicken Sie auf **📦 Stagebox Update** (Admin)
3. Aktuelle und verfügbare Versionen werden angezeigt
4. Klicken Sie auf **⬇️ Update installieren**, falls verfügbar
5. Warten Sie auf die Installation und den automatischen Neustart

<img src="screenshots/80-stagebox-update.png" width="450" alt="Stagebox Update Dialog">
<div style="page-break-before: always;"></div>

#### 2.8.2 System-Updates

Betriebssystem-Updates prüfen und installieren:

1. Gehen Sie zur Begrüssungsseite
2. Klicken Sie auf **🖥️ System-Updates** (Admin)
3. Sicherheits- und System-Updates werden aufgelistet
4. Klicken Sie auf **⬇️ Updates installieren**
5. Das System wird bei Bedarf neu gestartet

<img src="screenshots/81-system-updates.png" width="450" alt="System Updates Dialog">

---

<div style="page-break-before: always;"></div>

### 2.9 Berichte & Dokumentation

Stagebox bietet umfassende Berichtsfunktionen für professionelle Installationsdokumentation. Berichte enthalten Gerätebestände, Konfigurationsdetails und können mit Installateur-Branding angepasst werden.

#### 2.9.1 Installateur-Profil

Das Installateur-Profil enthält Ihre Firmeninformationen, die auf allen generierten Berichten erscheinen. Dies ist eine globale Einstellung, die für alle Gebäude gilt.

**Zugriff auf das Installateur-Profil:**

1. Gehen Sie zur Begrüssungsseite
2. Klicken Sie auf **🏢 Installateur-Profil** (Admin erforderlich)

**Verfügbare Felder:**

| Feld | Beschreibung |
|------|-------------|
| Firmenname | Ihr Firmen- oder Geschäftsname |
| Adresse | Strasse (mehrzeilig möglich) |
| Telefon | Kontakttelefonnummer |
| E-Mail | Kontakt-E-Mail-Adresse |
| Website | Firmen-Website-URL |
| Logo | Firmenlogo-Bild (PNG, JPG, max. 2MB) |

**Logo-Richtlinien:**
- Empfohlene Grösse: 400×200 Pixel oder ähnliches Seitenverhältnis
- Formate: PNG (transparenter Hintergrund empfohlen) oder JPG
- Maximale Dateigrösse: 2MB
- Das Logo erscheint in der Kopfzeile von PDF-Berichten

> **Tipp:** Vervollständigen Sie das Installateur-Profil, bevor Sie Ihren ersten Bericht erstellen, um eine professionelle Dokumentation sicherzustellen.

<img src="screenshots/90-installer-profile.png" width="450" alt="Installer Profile Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.2 Gebäudeprofil (Objektinformationen)

Jedes Gebäude kann ein eigenes Profil mit kunden- und projektspezifischen Informationen haben. Diese Daten erscheinen in den für dieses Gebäude generierten Berichten.

**Zugriff auf das Gebäudeprofil:**

1. Öffnen Sie die Gebäudeseite
2. Gehen Sie zum **Experten**-Bereich in der Seitenleiste
3. Klicken Sie auf **⚙️ Gebäudeeinstellungen**
4. Wählen Sie den **Objekt**-Tab

**Verfügbare Felder:**

| Feld | Beschreibung |
|------|-------------|
| Objektname | Projekt- oder Liegenschaftsname (z.B. «Villa Müller») |
| Kundenname | Name des Kunden |
| Adresse | Liegenschaftsadresse (mehrzeilig möglich) |
| Kontakttelefon | Telefonnummer des Kunden |
| Kontakt-E-Mail | E-Mail-Adresse des Kunden |
| Notizen | Zusätzliche Anmerkungen (erscheinen in Berichten) |

> **Hinweis:** Der Objektname wird als Berichtstitel verwendet. Wenn nicht gesetzt, wird stattdessen der Gebäudename verwendet.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Building Profile Tab">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Ein Snapshot erfasst den vollständigen Zustand aller Geräte in einem Gebäude zu einem bestimmten Zeitpunkt. Snapshots werden als ZIP-Pakete gespeichert, die Gerätedaten und Konfigurationsdateien enthalten.

**Snapshot erstellen:**

1. Öffnen Sie die Gebäudeseite
2. Gehen Sie zum **Audit**-Bereich in der Seitenleiste
3. Klicken Sie auf **📸 Snapshots**
4. Warten Sie, bis der Scan abgeschlossen ist

**Snapshot-Verwaltung:**

| Aktion | Beschreibung |
|--------|-------------|
| 📥 Herunterladen | Snapshot-ZIP-Paket herunterladen |
| 🗑️ Löschen | Snapshot entfernen |

**Snapshot-ZIP-Inhalte:**

Jeder Snapshot wird als ZIP-Datei gespeichert, die enthält:

| Datei | Beschreibung |
|-------|-------------|
| `snapshot.json` | Vollständige Gerätescan-Daten (IP, MAC, Konfiguration, Status) |
| `installer_profile.json` | Installateur-Firmeninformationen |
| `installer_logo.png` | Firmenlogo (falls konfiguriert) |
| `ip_state.json` | Gerätedatenbank mit Raum-/Standortzuweisungen |
| `building_profile.json` | Objekt-/Kundeninformationen |
| `config.yaml` | Gebäudekonfiguration |
| `shelly_model_map.yaml` | Benutzerdefinierte Modellnamen-Zuordnungen (falls konfiguriert) |
| `scripts/*.js` | Bereitgestellte Skripte (falls vorhanden) |

> **Tipp:** Snapshots sind eigenständige Pakete, die mit externen Dokumentationstools verwendet oder für zukünftige Referenz archiviert werden können.

**Automatische Bereinigung:**

Stagebox behält automatisch nur die 5 neuesten Snapshots pro Gebäude, um Speicherplatz zu sparen.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Snapshots Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.4 Berichtsgenerator

Professionelle Installationsberichte im PDF- oder Excel-Format generieren.

**Bericht erstellen:**

1. Öffnen Sie die Gebäudeseite
2. Gehen Sie zum **Audit**-Bereich in der Seitenleiste
3. Klicken Sie auf **📊 Berichtsgenerator**
4. Berichtsoptionen konfigurieren:
   - **Snapshot**: Neuen erstellen oder bestehenden Snapshot auswählen
   - **Sprache**: Berichtssprache (DE, EN, FR, IT, NL)
   - **Format**: PDF oder Excel (XLSX)
5. Klicken Sie auf **Generieren**

<img src="screenshots/93-report-generator.png" width="450" alt="Report Generator Dialog">

**PDF-Berichtsinhalte:**

Der PDF-Bericht enthält:
- **Kopfzeile**: Firmenlogo, Berichtstitel, Erstellungsdatum
- **Objektinformationen**: Kundenname, Adresse, Kontaktdaten
- **Zusammenfassung**: Gesamtzahl Geräte, Räume und Gerätetypen
- **Gerätetabelle**: Vollständiges Inventar mit QR-Codes

**Gerätetabellen-Spalten:**

| Spalte | Beschreibung |
|--------|-------------|
| QR | QR-Code mit Link zur Geräte-Weboberfläche |
| Raum | Zugewiesener Raum |
| Standort | Position innerhalb des Raums |
| Name | Anzeigename des Geräts |
| Modell | Gerätetyp |
| IP | Netzwerkadresse |
| FW | Firmware-Version |
| MAC | Letzte 6 Zeichen der MAC-Adresse |
| SWTAK | Feature-Flags (siehe unten) |

**Feature-Flags (SWTAK):**

Jedes Gerät zeigt, welche Features konfiguriert sind:

| Flag | Bedeutung | Quelle |
|------|-----------|--------|
| **S** | Scripts | Gerät hat Skripte installiert |
| **W** | Webhooks | Gerät hat Webhooks konfiguriert |
| **T** | Timers | Auto-On- oder Auto-Off-Timer aktiv |
| **A** | Schedules | Geplante Automatisierungen konfiguriert |
| **K** | KVS | Key-Value-Store-Einträge vorhanden |

Aktive Flags sind hervorgehoben, inaktive Flags sind ausgegraut.

**Excel-Bericht:**

Der Excel-Export enthält dieselben Informationen wie der PDF-Bericht im Tabellenformat:
- Einzelnes Arbeitsblatt mit allen Geräten
- Kopfzeile mit Bericht-Metadaten
- Legende zur Erklärung der SWTAK-Flags
- Spalten optimiert für Filtern und Sortieren

> **Tipp:** Verwenden Sie das Excel-Format, wenn Sie die Daten weiterverarbeiten oder benutzerdefinierte Dokumentation erstellen möchten.

<div style="page-break-before: always;"></div>

#### 2.9.5 Konfigurations-Audit

Die Audit-Funktion vergleicht den aktuellen Live-Zustand aller Geräte mit einem Referenz-Snapshot, um Konfigurationsänderungen, neue Geräte oder Offline-Geräte zu erkennen.

**Audit durchführen:**

1. Öffnen Sie die Gebäudeseite
2. Gehen Sie zum **Audit**-Bereich in der Seitenleiste
3. Klicken Sie auf **🔍 Audit starten**
4. Wählen Sie einen Referenz-Snapshot aus dem Dropdown
5. Klicken Sie auf **🔍 Audit starten**

<img src="screenshots/94-audit-setup.png" width="450" alt="Audit Setup Dialog">

Das System führt einen frischen Scan aller Geräte durch und vergleicht sie mit dem ausgewählten Snapshot.

**Audit-Ergebnisse:**

| Status | Symbol | Beschreibung |
|--------|--------|-------------|
| OK | ✅ | Gerät seit Snapshot unverändert |
| Geändert | ⚠️ | Konfigurationsunterschiede erkannt |
| Offline | ❌ | Gerät war im Snapshot, antwortet aber nicht |
| Neu | 🆕 | Gerät gefunden, das nicht im Snapshot war |

<img src="screenshots/95-audit-results.png" width="500" alt="Audit Results">

**Erkannte Änderungen:**

Das Audit erkennt und meldet:
- IP-Adressänderungen
- Änderungen des Gerätenamens
- Firmware-Updates
- Konfigurationsänderungen (Eingangstypen, Schaltereinstellungen, Rollladeneinstellungen)
- WLAN-Einstellungsänderungen
- Neue oder fehlende Geräte

**Anwendungsfälle:**

- **Nachinstallations-Überprüfung**: Bestätigen, dass alle Geräte wie dokumentiert konfiguriert sind
- **Wartungsprüfungen**: Unerwartete Änderungen seit dem letzten Besuch erkennen
- **Fehlerbehebung**: Identifizieren, welche Einstellungen geändert wurden
- **Übergabedokumentation**: Überprüfen, ob die Installation vor der Übergabe der Spezifikation entspricht

> **Tipp:** Erstellen Sie nach Abschluss einer Installation einen Snapshot, um ihn als Referenz für zukünftige Audits zu verwenden.

<div style="page-break-before: always;"></div>

## Anhang

### A. Tastenkürzel

| Tastenkürzel | Aktion |
|-------------|--------|
| `Escape` | Dialog/Modal schliessen |
| `Enter` | Dialog bestätigen |

### B. Statusanzeigen

| Symbol | Bedeutung |
|--------|-----------|
| 🟢 (grün) | Gerät online |
| 🔴 (rot) | Gerät offline |
| S1–S4 | Aktuelle Provisionierungsstufe |
| ⚡ | Firmware-Update verfügbar |

### C. Fehlerbehebung

**Web-UI nicht erreichbar:**
- Ethernet-Verbindung prüfen
- Prüfen, ob Stagebox eine IP hat (Router-DHCP-Liste oder OLED-Display)
- IP-Adresse direkt statt .local versuchen

**Admin-PIN vergessen:**
- OLED-Taste **10+ Sekunden** gedrückt halten
- Das Display zeigt «PIN RESET» und «PIN = 0000»
- Die PIN ist nun auf den Standard `0000` zurückgesetzt
- Mit `0000` anmelden und PIN sofort ändern

**Geräte werden in Stage 1 nicht gefunden:**
- Sicherstellen, dass das Gerät im AP-Modus ist (LED blinkt)
- Stagebox näher an das Gerät bringen
- WLAN-Adapter-Verbindung prüfen

**Geräte werden in Stage 2 nicht gefunden:**
- DHCP-Bereichseinstellungen prüfen
- Prüfen, ob das Gerät mit dem richtigen WLAN verbunden ist
- 30 Sekunden nach Stage 1 warten

**Stage 4 schlägt fehl:**
- Gerätekompatibilität prüfen
- Überprüfen, ob ein Profil für den Gerätetyp existiert
- Prüfen, ob das Gerät online ist

**USB-Backup-Fehler:**
- USB-Stick entfernen und erneut einstecken
- Bei anhaltendem Fehler Seite aktualisieren (Ctrl+F5)
- Sicherstellen, dass der USB-Stick für Stagebox formatiert ist (Admin → USB-Stick formatieren)

**Berichtserstellung langsam:**
- Grosse Installationen (50+ Geräte) können 10–20 Sekunden dauern
- PDF-Erstellung beinhaltet QR-Code-Generierung für jedes Gerät
- Excel-Format für schnellere Erstellung ohne QR-Codes verwenden

---

*Stagebox Web-UI Handbuch — Version 1.1.0*