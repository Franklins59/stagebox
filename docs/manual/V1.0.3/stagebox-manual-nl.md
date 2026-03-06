# Stagebox Web-UI Gebruikershandleiding

## Deel 1: Aan de slag

Deze handleiding begeleidt je door de eerste installatie van je Stagebox en het aanmaken van je eerste gebouwproject.
  



<img src="screenshots/01-stagebox-picture.png" width="700" alt="Productfoto">

### 1.1 De Stagebox aansluiten

1. Sluit de Stagebox aan op je netwerk met een Ethernet-kabel
2. Sluit de voeding aan
3. Wacht ongeveer 60 seconden tot het systeem is opgestart
4. Het OLED-display aan de voorkant toont verbindingsinformatie

> **Opmerking:** De Stagebox vereist een bekabelde netwerkverbinding. WiFi wordt alleen gebruikt voor het provisioneren van Shelly-apparaten.

<div style="page-break-before: always;"></div>

### 1.2 Het OLED-display gebruiken

De Stagebox heeft een ingebouwd OLED-display dat automatisch door verschillende informatieschermen roteert (elke 10 seconden).

**Scherm 1 - Splash (Hoofdidentificatie):**

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

Dit scherm toont:
- "STAGEBOX" titel
- IP-adres voor webtoegang
- MAC-suffix (laatste 6 tekens voor identificatie)

**Scherm 2 - Gebouwinfo:**
- Huidige Stagebox-versie
- Actieve gebouwnaam

**Scherm 3 - Systeemstatus:**
- CPU-temperatuur en belasting
- NVMe-temperatuur
- RAM- en schijfgebruik

**Scherm 4 - Netwerk:**
- Ethernet IP-adres
- WLAN IP-adres (indien verbonden)
- Hostnaam

**Scherm 5 - Klok:**
- Huidige tijd met seconden
- Huidige datum

<div style="page-break-before: always;"></div>

**OLED-knopfuncties:**

De knop op de Argon ONE behuizing bedient het display:

| Drukduur | Actie |
|----------|-------|
| Korte druk (<2s) | Naar volgend scherm |
| Lange druk (2-10s) | Display aan/uit |
| Zeer lange druk (10s+) | Admin-PIN resetten naar `0000` |

> **Tip:** Gebruik het Splash- of Netwerkscherm om het IP-adres te vinden dat nodig is voor toegang tot de Web-UI.

<div style="page-break-before: always;"></div>

### 1.3 Toegang tot de webinterface

Zoek het IP-adres op het OLED-display (Splash- of Netwerkscherm) en open vervolgens een webbrowser:

```
http://<IP-ADRES>:5000
```

Bijvoorbeeld: `http://192.168.1.100:5000`

**Alternatief met hostnaam:**

```
http://stagebox-XXXXXX.local:5000
```

Vervang `XXXXXX` door het MAC-suffix dat op het OLED-display wordt getoond.

> **Opmerking:** De `.local` hostnaam vereist mDNS-ondersteuning (Bonjour). Als het niet werkt, gebruik dan direct het IP-adres.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Welkomstpagina - Eerste toegang">
<div style="page-break-before: always;"></div>

### 1.4 Inloggen als Admin

Administratieve functies zijn beveiligd met een PIN. De standaard PIN is **0000**.

1. Klik op **🔒 Admin** in de Admin-sectie
2. Voer de PIN in (standaard: `0000`)
3. Klik op **Bevestigen**

Je bent nu ingelogd als Admin (weergegeven als 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Admin Login">

> **Beveiligingsaanbeveling:** Wijzig de standaard PIN direct na de eerste login (zie sectie 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Je eerste gebouw aanmaken

Een "gebouw" in Stagebox vertegenwoordigt een project of installatielocatie. Elk gebouw heeft zijn eigen apparatendatabase, IP-pool en configuratie.

1. Zorg dat je bent ingelogd als Admin (🔓 Admin zichtbaar)
2. Klik op **➕ Nieuw gebouw**
3. Voer een gebouwnaam in (bijv. `klant_huis`)
   - Gebruik alleen kleine letters, cijfers en underscores
   - Spaties en speciale tekens worden automatisch geconverteerd
4. Klik op **Aanmaken**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="Nieuw gebouw dialoog">

Het gebouw wordt aangemaakt en **opent automatisch** met de WiFi-configuratiedialoog.

---

> ⚠️ **KRITIEK: Configureer WiFi-instellingen correct!**
>
> De WiFi-instellingen die je hier invoert bepalen met welk netwerk je Shelly-apparaten verbinding maken. **Onjuiste instellingen maken apparaten onbereikbaar!**
>
> - Controleer de SSID-spelling (hoofdlettergevoelig!)
> - Controleer of het wachtwoord correct is
> - Zorg dat de IP-bereiken overeenkomen met je werkelijke netwerk
>
> Apparaten die zijn geprovisioneerd met verkeerde WiFi-gegevens moeten worden gereset naar fabrieksinstellingen en opnieuw worden geprovisioneerd.

<div style="page-break-before: always;"></div>

### 1.6 WiFi en IP-bereiken configureren

Na het aanmaken van een gebouw verschijnt automatisch de **Gebouwinstellingen** dialoog.

<img src="screenshots/07-building-settings.png" width="200" alt="Gebouwinstellingen">

#### WiFi-configuratie

Voer de WiFi-gegevens in waarmee Shelly-apparaten moeten verbinden:

**Primaire WiFi (vereist):**
- SSID: Je netwerknaam (bijv. `ThuisNetwerk`)
- Wachtwoord: Je WiFi-wachtwoord

**Backup WiFi (optioneel):**
- Een reservenetwerk als het primaire niet beschikbaar is

<img src="screenshots/08-wifi-settings.png" width="450" alt="WiFi-instellingen">

#### IP-adresbereiken

Configureer de statische IP-pool voor Shelly-apparaten:

**Shelly Pool:**
- Van: Eerste IP voor apparaten (bijv. `192.168.1.50`)
- Tot: Laatste IP voor apparaten (bijv. `192.168.1.99`)

**Gateway:**
- Meestal je router-IP (bijv. `192.168.1.1`)
- Leeg laten voor automatische detectie (.1)

**DHCP-scanbereik (optioneel):**
- Bereik waar nieuwe apparaten verschijnen na fabrieksreset
- Leeg laten om het hele subnet te scannen (langzamer)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="IP-bereikinstellingen">

> **Waarschuwing:** De IP-bereiken moeten overeenkomen met je werkelijke netwerk! Apparaten zijn onbereikbaar als ze zijn geconfigureerd met een verkeerd subnet.

5. Klik op **💾 Opslaan**

<div style="page-break-before: always;"></div>

### 1.7 Admin-PIN wijzigen

Om je Admin-PIN te wijzigen (standaard is `0000`):

1. Klik op **🔓 Admin** (moet ingelogd zijn)
2. Klik op **🔑 PIN wijzigen**
3. Voer de nieuwe PIN in (minimaal 4 cijfers)
4. Bevestig de nieuwe PIN
5. Klik op **Opslaan**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="PIN wijzigen dialoog">

> **Belangrijk:** Onthoud deze PIN! Deze beschermt alle administratieve functies inclusief het verwijderen van gebouwen en systeeminstellingen.

### 1.8 Volgende stappen

Je Stagebox is nu klaar voor apparaatprovisioning. Ga verder naar Deel 2 om meer te leren over:
- Provisioneren van nieuwe Shelly-apparaten (Stage 1-4)
- Apparaatbeheer
- Backups maken

---

<div style="page-break-before: always;"></div>

## Deel 2: Functiereferentie

### 2.1 Welkomstpagina (Gebouwselectie)

De welkomstpagina is het startpunt na toegang tot de Stagebox. Het toont alle gebouwen en biedt systeembrede functies.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Welkomstpagina overzicht">

#### 2.1.1 Gebouwenlijst

Het centrale gebied toont alle beschikbare gebouwen als kaarten.

Elke gebouwkaart toont:
- Gebouwnaam
- IP-bereik samenvatting
- Apparaataantal

**Acties (alleen Admin-modus):**
- ✏️ Gebouw hernoemen
- 🗑️ Gebouw verwijderen

<img src="screenshots/21-building-cards.png" width="200" alt="Gebouwkaarten">

**Een gebouw selecteren:**
- Enkele klik om te selecteren
- Dubbelklik om direct te openen
- Klik op **Openen →** na selectie

#### 2.1.2 Systeemsectie

Links van de gebouwenlijst:

| Knop | Functie | Admin vereist |
|------|---------|---------------|
| 💾 Backup naar USB | Backup van alle gebouwen maken op USB-stick | Nee |
| 🔄 Herstarten | Stagebox herstarten | Nee |
| ⏻ Afsluiten | Stagebox veilig afsluiten | Nee |

> **Belangrijk:** Gebruik altijd **Afsluiten** voordat je de stroom loskoppelt om datacorruptie te voorkomen.

#### 2.1.3 Admin-sectie

Administratieve functies (vereist Admin-PIN):

| Knop | Functie |
|------|---------|
| 🔒/🔓 Admin | Inloggen/Uitloggen |
| ➕ Nieuw gebouw | Nieuw gebouw aanmaken |
| 📤 Alle gebouwen exporteren | ZIP van alle gebouwen downloaden |
| 📥 Gebouw(en) importeren | Importeren uit ZIP-bestand |
| 📜 Shelly Script Pool | Gedeelde scripts beheren |
| 📂 Herstellen van USB | Gebouwen herstellen van USB-backup |
| 🔌 USB-stick formatteren | USB voorbereiden voor backups |
| 🔑 PIN wijzigen | Admin-PIN wijzigen |
| 📦 Stagebox Update | Controleren op software-updates |
| 🖥️ Systeem Updates | Controleren op OS-updates |
| 🌐 Taal | Interfacetaal wijzigen |
| 🏢 Installateur Profiel | Bedrijfsgegevens configureren voor rapporten |


#### 2.1.4 USB-backup

**Een backup maken:**

1. Steek een USB-stick in (elk formaat)
2. Indien niet geformatteerd voor Stagebox: Klik op **🔌 USB-stick formatteren** (Admin)
3. Klik op **💾 Backup naar USB**
4. Wacht op het voltooiingsbericht
5. De USB-stick kan nu veilig worden verwijderd

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="USB-formatteer dialoog">

**Herstellen van USB:**

1. Steek de USB-stick met backups in
2. Klik op **📂 Herstellen van USB** (Admin)
3. Selecteer een backup uit de lijst
4. Kies de gebouwen om te herstellen
5. Klik op **Geselecteerde herstellen**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="USB-herstel dialoog">

#### 2.1.5 Gebouwen exporteren/importeren

**Exporteren:**
1. Klik op **📤 Alle gebouwen exporteren** (Admin)
2. Een ZIP-bestand met alle gebouwdata wordt gedownload

**Importeren:**
1. Klik op **📥 Gebouw(en) importeren** (Admin)
2. Sleep een ZIP-bestand of klik om te selecteren
3. Kies welke gebouwen te importeren
4. Selecteer de actie voor bestaande gebouwen (overslaan/overschrijven)
5. Klik op **Geselecteerde importeren**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Gebouwen importeren dialoog">

<div style="page-break-before: always;"></div>

### 2.2 Gebouwpagina

De gebouwpagina is de hoofdwerkruimte voor provisioning en beheer van apparaten in een specifiek gebouw.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Gebouwpagina overzicht">

#### Layout:
- **Linker zijbalk:** Provisioningstages, filters, acties, instellingen
- **Centraal gebied:** Apparatenlijst
- **Rechter zijbalk:** Stage-panelen of apparaatdetails, Script-, KVS-, Webhook- en OTA-tabs

### 2.3 Linker zijbalk

#### 2.3.1 Gebouw-header

Toont de huidige gebouwnaam. Klik om terug te keren naar de welkomstpagina.
<div style="page-break-before: always;"></div>

#### 2.3.2 Provisioningstages

De 4-staps provisioningpipeline:

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Provisioningstages">

**S1 - AP-provisioning:**
- Zoekt naar Shelly-apparaten in AP-modus (Access Point)
- Configureert WiFi-gegevens
- Schakelt cloud, BLE en AP-modus uit

**S2 - Adopt:**
- Scant netwerk naar nieuwe apparaten (DHCP-bereik)
- Wijst statische IP's toe uit de pool
- Registreert apparaten in de database

**S3 - OTA & Namen:**
- Werkt firmware bij naar de nieuwste versie
- Synchroniseert vriendelijke namen naar apparaten

**S4 - Configureren:**
- Past apparaatprofielen toe
- Configureert ingangen, schakelaars, rolluiken, etc.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1: AP-provisioning

1. Klik op de **S1** knop
2. De Stagebox WiFi-adapter zoekt naar Shelly AP's
3. Gevonden apparaten worden automatisch geconfigureerd, de apparaatteller loopt op
4. Klik op **⏹ Stop** wanneer klaar

<img src="screenshots/32-stage1-panel.png" width="450" alt="Stage 1 paneel">

> **Tip:** Zet Shelly-apparaten in AP-modus door de knop 10+ seconden ingedrukt te houden of een fabrieksreset uit te voeren.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2: Adopt

1. Klik op de **S2** knop
2. Klik op **Netwerk scannen**
3. Nieuwe apparaten verschijnen in de lijst
4. Selecteer apparaten om te adopteren of klik op **Alles adopteren**
5. Apparaten krijgen statische IP's en worden geregistreerd

<img src="screenshots/33-stage2-panel.png" width="300" alt="Stage 2 paneel">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3: OTA & Namen

1. Klik op de **S3** knop
2. Apparaten in Stage 2 worden getoond
3. Klik op **Stage 3 uitvoeren** om:
   - Firmware bij te werken (indien nieuwere versie beschikbaar)
   - Vriendelijke namen te synchroniseren van database naar apparaten

<img src="screenshots/34-stage3-panel.png" width="300" alt="Stage 3 paneel">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4: Configureren

1. Klik op de **S4** knop
2. Apparaten in Stage 3 worden getoond
3. Klik op **Stage 4 uitvoeren** om profielen toe te passen:
   - Schakelaarinstellingen (beginstatus, auto-uit)
   - Rolluikinstellingen (richting omkeren, limieten)
   - Ingangconfiguraties
   - Aangepaste acties

<img src="screenshots/35-stage4-panel.png" width="300" alt="Stage 4 paneel">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filters

Filter de apparatenlijst op verschillende criteria:

| Filter | Beschrijving |
|--------|--------------|
| Stage | Apparaten in een specifieke provisioningstage tonen |
| Kamer | Apparaten in een specifieke kamer tonen |
| Model | Specifieke apparaattypes tonen |
| Status | Online/Offline apparaten |

<img src="screenshots/36-filter-panel.png" width="200" alt="Filter paneel">

#### 2.3.8 Acties

Bulkoperaties op geselecteerde apparaten:

| Actie | Beschrijving |
|-------|--------------|
| 🔄 Verversen | Apparaatstatus bijwerken |
| 📋 Kopiëren | Apparaatinfo naar klembord kopiëren |
| 📤 CSV exporteren | Geselecteerde apparaten exporteren |
| 🗑️ Verwijderen | Uit database verwijderen (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Apparatenlijst

Het centrale gebied toont alle apparaten in het huidige gebouw.

<img src="screenshots/40-device-list.png" width="500" alt="Apparatenlijst">

#### Kolommen:

| Kolom | Beschrijving |
|-------|--------------|
| ☑️ | Selectievakje |
| Status | Online (🟢) / Offline (🔴) |
| Naam | Apparaat vriendelijke naam |
| Kamer | Toegewezen kamer |
| Locatie | Positie in kamer |
| Model | Apparaattype |
| IP | Huidig IP-adres |
| Stage | Huidige provisioningstage (S1-S4) |

#### Selectie:
- Klik op vakje om individuele apparaten te selecteren
- Klik op header-vakje om alle zichtbare te selecteren
- Shift+klik voor bereikselectie

#### Sorteren:
- Klik op kolomheader om te sorteren
- Klik opnieuw voor omgekeerde volgorde

<div style="page-break-before: always;"></div>

### 2.5 Rechter zijbalk (Apparaatdetails)

Wanneer een apparaat is geselecteerd, toont de rechter zijbalk gedetailleerde informatie en acties.

#### 2.5.1 Apparaat Info Tab

Basis apparaatinformatie:

| Veld | Beschrijving |
|------|--------------|
| Naam | Bewerkbare vriendelijke naam |
| Kamer | Kamertoewijzing (bewerkbaar) |
| Locatie | Positie in kamer (bewerkbaar) |
| MAC | Hardware-adres |
| IP | Netwerkadres |
| Model | Hardware model |
| Firmware | Huidige versie |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Apparaat Info Tab">

<div style="page-break-before: always;"></div>

#### 2.5.2 Scripts Tab

Scripts op het geselecteerde apparaat beheren:

- Geïnstalleerde scripts bekijken
- Scripts starten/stoppen
- Scripts verwijderen
- Nieuwe scripts deployen

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Apparaat Scripts Tab">

#### 2.5.3 KVS Tab

Key-Value Store entries bekijken en bewerken:

- Systeemwaarden (alleen-lezen)
- Gebruikerswaarden (bewerkbaar)
- Nieuwe entries toevoegen
- Entries verwijderen

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Apparaat KVS Tab">
<div style="page-break-before: always;"></div>

#### 2.5.4 Webhooks Tab

Apparaat webhooks configureren:

- Bestaande webhooks bekijken
- Nieuwe webhooks toevoegen
- URL's en condities bewerken
- Webhooks verwijderen

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Apparaat Webhooks Tab">

#### 2.5.5 Planningen Tab

Geplande taken beheren:

- Bestaande planningen bekijken
- Tijdgebaseerde automatiseringen toevoegen
- Planningen in-/uitschakelen
- Planningen verwijderen

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Apparaat Planningen Tab">

#### 2.5.6 Virtuele Componenten Tab

Virtuele componenten op apparaten configureren:

- Virtuele schakelaars
- Virtuele sensoren
- Tekst componenten
- Nummer componenten

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Apparaat Virtuals Tab">

#### 2.5.7 FW-Updates Tab

Apparaat firmware beheren:

- Huidige versie bekijken
- Controleren op updates
- Firmware-updates toepassen

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Apparaat FW-Updates Tab">
<div style="page-break-before: always;"></div>

### 2.6 Scriptbeheer

#### 2.6.1 Script Pool (Admin)

Gedeelde scripts beheren die beschikbaar zijn voor deployment:

1. Ga naar de welkomstpagina
2. Klik op **📜 Shelly Script Pool** (Admin)
3. Upload JavaScript-bestanden (.js)
4. Verwijder ongebruikte scripts

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Script Pool dialoog">
<div style="page-break-before: always;"></div>

#### 2.6.2 Scripts deployen

1. Selecteer doelapparate(n) in de lijst
2. Ga naar de **Scripts** tab
3. Selecteer bron: **Lokaal** (Script Pool) of **GitHub Bibliotheek**
4. Kies een script
5. Configureer opties:
   - ☑️ Uitvoeren bij opstarten
   - ☑️ Starten na deploy
6. Klik op **📤 Deployen**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Script Deploy dialoog">

<div style="page-break-before: always;"></div>

### 2.7 Expert-instellingen (Geavanceerd)

> ⚠️ **Waarschuwing:** De Expert-instellingen maken directe configuratie van provisioninggedrag en systeemparameters mogelijk. Onjuiste wijzigingen kunnen apparaatprovisioning beïnvloeden. Gebruik met voorzichtigheid!

Toegang via de **Expert** sectie → **⚙️ Gebouwinstellingen** in de gebouwpagina zijbalk.

De Gebouwinstellingen dialoog biedt een interface met tabs voor het configureren van geavanceerde opties.

---

#### 2.7.1 Provisioning Tab

Bepaalt het gedrag van Stage 1 (AP-modus) provisioning.

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Expert Provisioning Tab">

| Instelling | Beschrijving | Standaard |
|------------|--------------|-----------|
| **Loop-modus** | Continu zoeken naar nieuwe apparaten. Indien ingeschakeld blijft Stage 1 zoeken naar nieuwe Shelly AP's na elke succesvolle provisioning. Uitschakelen voor provisioning van één apparaat. | ☑️ Aan |
| **AP uitschakelen na provisioning** | WiFi Access Point van apparaat uitschakelen na verbinding met je netwerk. Aanbevolen voor beveiliging. | ☑️ Aan |
| **Bluetooth uitschakelen** | Bluetooth uitschakelen op geprovisioneerde apparaten. Bespaart energie en verkleint aanvalsoppervlak. | ☑️ Aan |
| **Cloud uitschakelen** | Shelly Cloud-connectiviteit uitschakelen. Apparaten zijn alleen lokaal bereikbaar. | ☑️ Aan |
| **MQTT uitschakelen** | MQTT-protocol uitschakelen op apparaten. Inschakelen als je een domoticasysteem met MQTT gebruikt. | ☑️ Aan |

---

#### 2.7.2 OTA & Namen Tab

Configureer firmware-updategedrag en vriendelijke namen behandeling tijdens Stage 3.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Expert OTA Tab">

**Firmware Updates (OTA):**

| Instelling | Beschrijving | Standaard |
|------------|--------------|-----------|
| **OTA-updates inschakelen** | Controleren en optioneel installeren van firmware-updates tijdens Stage 3. | ☑️ Aan |
| **Update-modus** | `Alleen controleren`: Beschikbare updates rapporteren zonder te installeren. `Controleren & Updaten`: Beschikbare updates automatisch installeren. | Alleen controleren |
| **Timeout (seconden)** | Maximale wachttijd voor OTA-operaties. Verhogen voor trage netwerken. | 20 |

**Vriendelijke Namen:**

| Instelling | Beschrijving | Standaard |
|------------|--------------|-----------|
| **Vriendelijke namen inschakelen** | Kamer/locatienamen toepassen op apparaten tijdens Stage 3. Namen worden opgeslagen in de apparaatconfiguratie. | ☑️ Aan |
| **Ontbrekende namen aanvullen** | Automatisch namen genereren voor apparaten zonder toewijzing. Gebruikt het patroon `<Model>_<MAC-suffix>`. | ☐ Uit |

<div style="page-break-before: always;"></div>

#### 2.7.3 Export Tab

Configureer CSV-exportinstellingen voor apparaatlabels en rapporten.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Expert Export Tab">

**CSV-scheidingsteken:**

Kies het kolomscheidingsteken voor geëxporteerde CSV-bestanden:
- **Puntkomma (;)** - Standaard, werkt met Europese Excel-versies
- **Komma (,)** - Standaard CSV-formaat
- **Tab** - Voor tab-gescheiden waarden

**Standaardkolommen:**

Selecteer welke kolommen verschijnen in geëxporteerde CSV-bestanden. Beschikbare kolommen:

| Kolom | Beschrijving |
|-------|--------------|
| `id` | Apparaat MAC-adres (unieke identifier) |
| `ip` | Huidig IP-adres |
| `hostname` | Apparaat hostnaam |
| `fw` | Firmwareversie |
| `model` | Vriendelijke modelnaam |
| `hw_model` | Hardware model ID |
| `friendly_name` | Toegewezen apparaatnaam |
| `room` | Kamertoewijzing |
| `location` | Locatie in kamer |
| `assigned_at` | Wanneer apparaat is geprovisioneerd |
| `last_seen` | Laatste communicatie timestamp |
| `stage3_friendly_status` | Naamtoewijzingsstatus |
| `stage3_ota_status` | Firmware-updatestatus |
| `stage4_status_result` | Configuratiestage resultaat |

<div style="page-break-before: always;"></div>

#### 2.7.4 Model Map Tab

Definieer aangepaste weergavenamen voor Shelly hardware model ID's.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Expert Model Map Tab">

De Model Map vertaalt interne hardware-identifiers (bijv. `SNSW-001X16EU`) naar leesbare namen (bijv. `Shelly Plus 1`).

**Gebruik:**
1. Voer de **Hardware ID** exact in zoals gerapporteerd door het apparaat
2. Voer je gewenste **Weergavenaam** in
3. Klik op **+ Model toevoegen** voor meer entries
4. Klik op **🗑️** om een entry te verwijderen

> **Tip:** Controleer de webinterface van het apparaat of de API-respons om de exacte hardware ID-string te vinden.

<div style="page-break-before: always;"></div>

#### 2.7.5 Geavanceerd Tab (YAML-editor)

Directe bewerking van configuratiebestanden voor geavanceerde scenario's.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Expert Geavanceerd Tab">

**Beschikbare bestanden:**

| Bestand | Beschrijving |
|---------|--------------|
| `config.yaml` | Hoofdgebouwconfiguratie (IP-bereiken, apparatendatabase, provisioninginstellingen) |
| `profiles/*.yaml` | Apparaatconfiguratieprofielen voor Stage 4 |

**Functies:**
- Syntaxvalidatie (groene/rode indicator)
- Selecteer bestand uit dropdown
- Bewerk inhoud direct
- Alle wijzigingen worden automatisch geback-upt voor opslaan

**Validatie-indicator:**
- 🟢 Groen: Geldige YAML-syntax
- 🔴 Rood: Syntaxfout (hover voor details)

> **Aanbeveling:** Gebruik de andere tabs voor normale configuratie. Gebruik de YAML-editor alleen wanneer je instellingen moet wijzigen die niet in de UI beschikbaar zijn, of voor probleemoplossing.

<div style="page-break-before: always;"></div>

### 2.8 Systeemonderhoud

#### 2.8.1 Stagebox Updates

Controleren en installeren van Stagebox software-updates:

1. Ga naar de welkomstpagina
2. Klik op **📦 Stagebox Update** (Admin)
3. Huidige en beschikbare versies worden getoond
4. Klik op **⬇️ Update installeren** indien beschikbaar
5. Wacht op installatie en automatische herstart

<img src="screenshots/80-stagebox-update.png" width="450" alt="Stagebox Update dialoog">
<div style="page-break-before: always;"></div>

#### 2.8.2 Systeem Updates

Controleren en installeren van besturingssysteem-updates:

1. Ga naar de welkomstpagina
2. Klik op **🖥️ Systeem Updates** (Admin)
3. Beveiligings- en systeemupdates worden getoond
4. Klik op **⬇️ Updates installeren**
5. Systeem kan herstarten indien nodig

<img src="screenshots/81-system-updates.png" width="450" alt="Systeem Updates dialoog">

---

<div style="page-break-before: always;"></div>

### 2.9 Rapporten & Documentatie

Stagebox biedt uitgebreide rapportagefuncties voor professionele installatiedocumentatie. Rapporten bevatten apparaatinventarissen, configuratiedetails, en kunnen worden aangepast met installateurbranding.

#### 2.9.1 Installateur Profiel

Het installateur profiel bevat je bedrijfsinformatie die op alle gegenereerde rapporten verschijnt. Dit is een globale instelling die wordt gedeeld tussen alle gebouwen.

**Toegang tot het installateur profiel:**

1. Ga naar de welkomstpagina
2. Klik op **🏢 Installateur Profiel** (Admin vereist)

**Beschikbare velden:**

| Veld | Beschrijving |
|------|--------------|
| Bedrijfsnaam | Je bedrijfs- of handelsnaam |
| Adres | Postadres (meerregelig ondersteund) |
| Telefoon | Contacttelefoonnummer |
| E-mail | Contact e-mailadres |
| Website | Bedrijfswebsite URL |
| Logo | Bedrijfslogo afbeelding (PNG, JPG, max 2MB) |

**Logo-richtlijnen:**
- Aanbevolen formaat: 400×200 pixels of vergelijkbare verhouding
- Formaten: PNG (transparante achtergrond aanbevolen) of JPG
- Maximale bestandsgrootte: 2MB
- Het logo verschijnt in de header van PDF-rapporten

> **Tip:** Vul het installateur profiel in voordat je je eerste rapport genereert om professioneel ogende documentatie te verzekeren.

<img src="screenshots/90-installer-profile.png" width="450" alt="Installateur Profiel dialoog">

<div style="page-break-before: always;"></div>

#### 2.9.2 Gebouwprofiel (Objectinformatie)

Elk gebouw kan zijn eigen profiel hebben met klant- en projectspecifieke informatie. Deze gegevens verschijnen in rapporten die voor dat gebouw worden gegenereerd.

**Toegang tot gebouwprofiel:**

1. Open de gebouwpagina
2. Ga naar de **Expert** sectie in de zijbalk
3. Klik op **⚙️ Gebouwinstellingen**
4. Selecteer de **Object** tab

**Beschikbare velden:**

| Veld | Beschrijving |
|------|--------------|
| Objectnaam | Project- of eigendomsnaam (bijv. "Villa Müller") |
| Klantnaam | Naam van de klant |
| Adres | Eigendomsadres (meerregelig ondersteund) |
| Contacttelefoon | Telefoonnummer van de klant |
| Contact e-mail | E-mailadres van de klant |
| Notities | Aanvullende notities (verschijnen in rapporten) |

> **Opmerking:** De objectnaam wordt gebruikt als rapporttitel. Indien niet ingesteld, wordt de gebouwnaam gebruikt.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Gebouwprofiel Tab">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Een snapshot legt de volledige status van alle apparaten in een gebouw vast op een specifiek moment. Snapshots worden opgeslagen als ZIP-bundels met apparaatgegevens en configuratiebestanden.

**Een snapshot maken:**

1. Open de gebouwpagina
2. Ga naar de **Audit** sectie in de zijbalk
3. Klik op **📸 Snapshots**
4. Wacht tot de scan is voltooid

**Snapshotbeheer:**

| Actie | Beschrijving |
|-------|--------------|
| 📥 Downloaden | Download snapshot ZIP-bundel |
| 🗑️ Verwijderen | Verwijder snapshot |

**Snapshot ZIP-inhoud:**

Elke snapshot wordt opgeslagen als ZIP-bestand met:

| Bestand | Beschrijving |
|---------|--------------|
| `snapshot.json` | Volledige apparaatscangegevens (IP, MAC, config, status) |
| `installer_profile.json` | Installateur bedrijfsinformatie |
| `installer_logo.png` | Bedrijfslogo (indien geconfigureerd) |
| `ip_state.json` | Apparatendatabase met kamer/locatietoewijzingen |
| `building_profile.json` | Object/klantinformatie |
| `config.yaml` | Gebouwconfiguratie |
| `shelly_model_map.yaml` | Aangepaste modelnaam-mappings (indien geconfigureerd) |
| `scripts/*.js` | Gedeployde scripts (indien aanwezig) |

> **Tip:** Snapshots zijn zelfstandige bundels die kunnen worden gebruikt met externe documentatietools of gearchiveerd voor toekomstige referentie.

**Automatische opruiming:**

Stagebox bewaart automatisch alleen de 5 meest recente snapshots per gebouw om opslagruimte te besparen.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Snapshots dialoog">

<div style="page-break-before: always;"></div>

#### 2.9.4 Rapportgenerator

Genereer professionele installatierapporten in PDF- of Excel-formaat.

**Een rapport genereren:**

1. Open de gebouwpagina
2. Ga naar de **Audit** sectie in de zijbalk
3. Klik op **📊 Rapportgenerator**
4. Configureer rapportopties:
   - **Snapshot**: Nieuwe maken of bestaande selecteren
   - **Taal**: Rapporttaal (DE, EN, FR, IT, NL)
   - **Formaat**: PDF of Excel (XLSX)
5. Klik op **Genereren**

<img src="screenshots/93-report-generator.png" width="450" alt="Rapportgenerator dialoog">

**PDF-rapportinhoud:**

Het PDF-rapport bevat:
- **Header**: Bedrijfslogo, rapporttitel, generatiedatum
- **Objectinformatie**: Klantnaam, adres, contactgegevens
- **Samenvatting**: Totaal apparaten, kamers en apparaattypes
- **Apparatentabel**: Volledige inventaris met QR-codes

**Apparatentabel kolommen:**

| Kolom | Beschrijving |
|-------|--------------|
| QR | QR-code linkt naar apparaat webinterface |
| Kamer | Toegewezen kamer |
| Locatie | Positie in kamer |
| Naam | Apparaat vriendelijke naam |
| Model | Apparaattype |
| IP | Netwerkadres |
| FW | Firmwareversie |
| MAC | Laatste 6 tekens van MAC-adres |
| SWTAK | Feature-vlaggen (zie hieronder) |

**Feature-vlaggen (SWTAK):**

Elk apparaat toont welke features zijn geconfigureerd:

| Vlag | Betekenis | Bron |
|------|-----------|------|
| **S** | Scripts | Apparaat heeft scripts geïnstalleerd |
| **W** | Webhooks | Apparaat heeft webhooks geconfigureerd |
| **T** | Timers | Auto-aan of auto-uit timers actief |
| **A** | Planningen | Geplande automatiseringen geconfigureerd |
| **K** | KVS | Key-Value Store entries aanwezig |

Actieve vlaggen zijn gemarkeerd, inactieve vlaggen zijn grijs.

**Excel-rapport:**

De Excel-export bevat dezelfde informatie als de PDF in spreadsheetformaat:
- Enkel werkblad met alle apparaten
- Header met rapportmetadata
- Legenda die de SWTAK-vlaggen uitlegt
- Kolommen geoptimaliseerd voor filteren en sorteren

> **Tip:** Gebruik Excel-formaat wanneer je de gegevens verder moet verwerken of aangepaste documentatie moet maken.

<div style="page-break-before: always;"></div>

#### 2.9.5 Configuratie-audit

De Audit-functie vergelijkt de huidige live-status van alle apparaten met een referentie-snapshot om configuratiewijzigingen, nieuwe apparaten of offline apparaten te detecteren.

**Een audit uitvoeren:**

1. Open de gebouwpagina
2. Ga naar de **Audit** sectie in de zijbalk
3. Klik op **🔍 Audit uitvoeren**
4. Selecteer een referentie-snapshot uit het dropdown-menu
5. Klik op **🔍 Audit starten**

<img src="screenshots/94-audit-setup.png" width="450" alt="Audit setup dialoog">

Het systeem voert een nieuwe scan uit van alle apparaten en vergelijkt ze met de geselecteerde snapshot.

**Audit-resultaten:**

| Status | Icoon | Beschrijving |
|--------|-------|--------------|
| OK | ✅ | Apparaat ongewijzigd sinds snapshot |
| Gewijzigd | ⚠️ | Configuratieverschillen gedetecteerd |
| Offline | ❌ | Apparaat was in snapshot maar reageert niet |
| Nieuw | 🆕 | Apparaat gevonden dat niet in snapshot was |

<img src="screenshots/95-audit-results.png" width="500" alt="Audit-resultaten">

**Gedetecteerde wijzigingen:**

De audit detecteert en rapporteert:
- IP-adreswijzigingen
- Apparaatnaamwijzigingen
- Firmware-updates
- Configuratiewijzigingen (ingangtypes, schakelaarinstellingen, rolluikinstellingen)
- WiFi-instellingswijzigingen
- Nieuwe of ontbrekende apparaten

**Gebruiksscenario's:**

- **Post-installatie verificatie**: Bevestig dat alle apparaten zijn geconfigureerd zoals gedocumenteerd
- **Onderhoudscontroles**: Detecteer onverwachte wijzigingen sinds het laatste bezoek
- **Probleemoplossing**: Identificeer welke instellingen zijn gewijzigd
- **Opleverdocumentatie**: Verifieer dat installatie overeenkomt met specificatie voor oplevering

> **Tip:** Maak een snapshot na het voltooien van een installatie om te gebruiken als referentie voor toekomstige audits.

<div style="page-break-before: always;"></div>

## Bijlage

### A. Sneltoetsen

| Sneltoets | Actie |
|-----------|-------|
| `Escape` | Dialoog/modal sluiten |
| `Enter` | Dialoog bevestigen |

### B. Statusindicatoren

| Icoon | Betekenis |
|-------|-----------|
| 🟢 (groen) | Apparaat online |
| 🔴 (rood) | Apparaat offline |
| S1-S4 | Huidige provisioningstage |
| ⚡ | Firmware-update beschikbaar |

### C. Probleemoplossing

**Kan geen toegang krijgen tot webinterface:**
- Controleer Ethernet-verbinding
- Controleer of Stagebox een IP heeft (router DHCP-lijst of OLED-display)
- Probeer IP-adres direct in plaats van .local

**Admin-PIN vergeten:**
- Houd de OLED-knop **10+ seconden** ingedrukt
- Display toont "PIN RESET" en "PIN = 0000"
- PIN is nu gereset naar standaard `0000`
- Log in met `0000` en wijzig PIN onmiddellijk

**Apparaten niet gevonden in Stage 1:**
- Zorg dat apparaat in AP-modus is (LED knippert)
- Breng Stagebox dichter bij apparaat
- Controleer WiFi-adapterverbinding

**Apparaten niet gevonden in Stage 2:**
- Controleer DHCP-bereikinstellingen
- Controleer of apparaat met juiste WiFi is verbonden
- Wacht 30 seconden na Stage 1

**Stage 4 mislukt:**
- Controleer apparaatcompatibiliteit
- Controleer of profiel bestaat voor apparaattype
- Controleer of apparaat online is

**USB-backupfouten:**
- Verwijder en plaats USB-stick opnieuw
- Als fout aanhoudt, ververs pagina (Ctrl+F5)
- Zorg dat USB-stick is geformatteerd voor Stagebox (Admin → USB-stick formatteren)

**Rapportgeneratie traag:**
- Grote installaties (50+ apparaten) kunnen 10-20 seconden duren
- PDF-generatie maakt QR-codes voor elk apparaat
- Gebruik Excel-formaat voor snellere generatie zonder QR-codes

---

*Stagebox Web-UI Gebruikershandleiding - Versie 1.5*