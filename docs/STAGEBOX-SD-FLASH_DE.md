# Stagebox Personal - SD-Karte flashen

Anleitung zum Übertragen des Stagebox Personal Images auf eine SD-Karte.

## Was Sie benötigen

- **SD-Karte**: Mindestens 8 GB, empfohlen 16 GB oder mehr
- **SD-Kartenleser**: USB-Adapter oder eingebauter Kartenslot
- **Raspberry Pi Imager**: Kostenlose Software von Raspberry Pi
- **Raspberry Pi 4 oder 5**

## Schritt 1: Image herunterladen

Laden Sie das aktuelle Stagebox Personal Image herunter:

🔗 **Download:** [https://github.com/franklins59/stagebox/releases/latest](https://github.com/franklins59/stagebox/releases/latest)

Laden Sie die Datei `stagebox-personal-vX.Y.Z.img.gz` herunter (ca. 1-2 GB).

## Schritt 2: Raspberry Pi Imager installieren

Laden Sie den **Raspberry Pi Imager** herunter und installieren Sie ihn:

🔗 **Download:** [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

Verfügbar für:
- Windows
- macOS
- Ubuntu/Linux

## Schritt 3: Image flashen

1. **SD-Karte einlegen**
   - Stecken Sie die SD-Karte in Ihren Computer

2. **Raspberry Pi Imager starten**

3. **Gerät wählen**
   - Klicken Sie auf "CHOOSE DEVICE"
   - Wählen Sie "Raspberry Pi 4" oder "Raspberry Pi 5"

4. **Betriebssystem wählen**
   - Klicken Sie auf "CHOOSE OS"
   - Scrollen Sie ganz nach unten
   - Wählen Sie "Use custom"
   - Navigieren Sie zur heruntergeladenen Datei `stagebox-personal-....img.gz`
   - **Hinweis:** Die .gz-Datei muss NICHT entpackt werden!

5. **SD-Karte wählen**
   - Klicken Sie auf "CHOOSE STORAGE"
   - Wählen Sie Ihre SD-Karte aus
   - ⚠️ **Achtung:** Wählen Sie die richtige Karte - alle Daten werden gelöscht!

6. **Einstellungen überspringen**
   - Wenn gefragt "Would you like to apply OS customisation settings?" → **NEIN** wählen
   - Die Stagebox-Einstellungen sind bereits im Image enthalten

7. **Schreiben starten**
   - Klicken Sie auf "WRITE"
   - Bestätigen Sie mit "YES"
   - Warten Sie bis der Vorgang abgeschlossen ist

### Hinweis zum Fortschritt (>100%)

Der Raspberry Pi Imager zeigt manchmal einen Fortschritt von über 100% an (z.B. 250% oder 457%). **Das ist normal und kein Fehler!**

**Warum passiert das?**
Das Image ist komprimiert (.gz-Format). Der Imager berechnet den Fortschritt basierend auf der komprimierten Dateigrösse (~1.5 GB), schreibt aber die entpackten Daten (~4-7 GB). Dadurch wird der angezeigte Wert grösser als 100%.

**Einfach abwarten** – der Vorgang wird erfolgreich abgeschlossen.

## Schritt 4: Erster Start (First Boot)

Nach dem Flashen:

1. **SD-Karte entnehmen** und in den Raspberry Pi einsetzen
2. **Netzwerkkabel anschliessen** (Ethernet empfohlen)
3. **Strom anschliessen**

### Was passiert beim ersten Start?

Der erste Start dauert **2-3 Minuten** länger als normal. Folgendes wird automatisch eingerichtet:

| Phase | Was passiert | Dauer |
|-------|--------------|-------|
| 1. Partition erweitern | SD-Karte wird vollständig genutzt | ~1-2 Min |
| 2. Sicherheitsschlüssel | SSH-Schlüssel werden generiert | ~10 Sek |
| 3. Hostname setzen | Gerät erhält eindeutigen Namen | ~5 Sek |
| 4. Stagebox starten | Web-Oberfläche wird gestartet | ~30 Sek |

**Erkennungszeichen:**
- Die grüne LED am Pi blinkt intensiv während der Einrichtung
- Nach Abschluss blinkt sie nur noch gelegentlich

### Wann ist die Stagebox bereit?

Die Stagebox ist bereit, wenn Sie die Web-Oberfläche erreichen können:

1. **IP-Adresse finden**
   - Schauen Sie in Ihrem Router nach dem neuen Gerät
   - Der Hostname beginnt mit `stagebox-` (z.B. `stagebox-a1b2c3`)

2. **Web-Oberfläche öffnen**
   - Öffnen Sie einen Browser
   - Geben Sie ein: `http://[IP-ADRESSE]:5000`
   - Beispiel: `http://192.168.1.100:5000`

## Häufige Fragen

### Die Web-Oberfläche ist nicht erreichbar?

- Warten Sie 3-4 Minuten nach dem Einschalten
- Prüfen Sie, ob das Netzwerkkabel richtig eingesteckt ist
- Prüfen Sie, ob die grüne LED noch stark blinkt (dann noch warten)

### Welche SD-Karte ist empfohlen?

| Typ | Geschwindigkeit | Empfehlung |
|-----|-----------------|------------|
| SanDisk Ultra | Gut | ✓ Funktioniert |
| SanDisk Extreme | Sehr gut | ✓✓ Empfohlen |
| SanDisk Extreme Pro | Exzellent | ✓✓✓ Beste Wahl |
| No-Name Karten | Variabel | ⚠️ Nicht empfohlen |

Mindestens **Class 10** oder **A1** Rating.

### Kann ich das Image auf mehrere SD-Karten flashen?

Ja! Jede Stagebox erhält beim ersten Start automatisch:
- Einen eindeutigen Hostnamen
- Eigene Sicherheitsschlüssel
- Eine eigene Geräte-ID

Sie können das gleiche Image beliebig oft verwenden.

### Muss ich die .gz-Datei entpacken?

**Nein!** Der Raspberry Pi Imager kann komprimierte .gz-Dateien direkt lesen. Das Entpacken ist nicht nötig und würde nur zusätzlichen Speicherplatz verbrauchen.

### Wie erhalte ich Updates?

Stagebox Personal erhält Updates direkt von GitHub. In der Web-Oberfläche unter **System → Updates** können Sie nach neuen Versionen suchen und diese installieren.

## Support & Community

Stagebox Personal ist Open Source. Bei Fragen oder Problemen:

- 🐛 **Issues:** [github.com/franklins59/stagebox/issues](https://github.com/franklins59/stagebox/issues)
- 📖 **Dokumentation:** [github.com/franklins59/stagebox](https://github.com/franklins59/stagebox)
- 🌐 **Webseite:** [franklins.forstec.ch](https://franklins.forstec.ch)

---

**Stagebox Pro** mit erweiterten Funktionen (Multi-Building, USB-Backup, Snapshots) ist als Hardware-Produkt erhältlich: [franklins.forstec.ch](https://franklins.forstec.ch)