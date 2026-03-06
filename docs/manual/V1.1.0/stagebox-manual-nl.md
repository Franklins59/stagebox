# Stagebox Web-UI Gebruikershandleiding

> *Deze handleiding correspondeert met Stagebox Pro Versie 1.1.0*

## Deel 1: Aan de slag

Deze handleiding begeleidt u bij de eerste configuratie van uw Stagebox en het aanmaken van uw eerste gebouwproject.
  


<img src="screenshots/01-stagebox-picture.png" width="700" alt="Product Picture">

### 1.1 De Stagebox aansluiten

1. Verbind de Stagebox met uw netwerk via een Ethernet-kabel
2. Sluit de voeding aan
3. Wacht ongeveer 60 seconden tot het systeem is opgestart
4. Het OLED-display aan de voorkant toont de verbindingsinformatie

> **Opmerking:** De Stagebox vereist een bekabelde netwerkverbinding. WiFi wordt alleen gebruikt voor het provisioneren van Shelly-apparaten.

<div style="page-break-before: always;"></div>

### 1.2 Het OLED-display gebruiken

De Stagebox beschikt over een ingebouwd OLED-display dat automatisch wisselt tussen meerdere informatieschermen (elke 10 seconden).

**Scherm 1 — Splash (Hoofdidentificatie):**

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
- «STAGEBOX»-titel
- IP-adres voor webtoegang
- MAC-suffix (laatste 6 tekens voor identificatie)

**Scherm 2 — Gebouwinformatie:**
- Huidige Stagebox-versie
- Actieve gebouwnaam

**Scherm 3 — Systeemstatus:**
- CPU-temperatuur en -belasting
- NVMe-temperatuur
- RAM- en schijfgebruik

**Scherm 4 — Netwerk:**
- Ethernet-IP-adres
- WLAN-IP-adres (indien verbonden)
- Hostnaam

**Scherm 5 — Klok:**
- Huidige tijd met seconden
- Huidige datum

<div style="page-break-before: always;"></div>

**OLED-knopfuncties:**

De knop op de Argon ONE-behuizing bedient het display:

| Drukduur | Actie |
|----------|-------|
| Korte druk (<2s) | Naar volgend scherm schakelen |
| Lange druk (2–10s) | Display in-/uitschakelen |
| Zeer lange druk (10s+) | Admin-PIN resetten naar `0000` |

> **Tip:** Gebruik het Splash- of Netwerkscherm om het IP-adres te vinden dat nodig is voor toegang tot de Web-UI.

<div style="page-break-before: always;"></div>

### 1.3 Toegang tot de webinterface

Zoek het IP-adres op het OLED-display (Splash- of Netwerkscherm) en open een webbrowser:

```
http://<IP-ADRES>:5000
```

Bijvoorbeeld: `http://192.168.1.100:5000`

**Alternatief via hostnaam:**

```
http://stagebox-XXXXXX.local:5000
```

Vervang `XXXXXX` door het MAC-suffix dat op het OLED-display wordt getoond.

> **Opmerking:** De `.local`-hostnaam vereist mDNS-ondersteuning (Bonjour). Als het niet werkt, gebruik dan direct het IP-adres.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Greeting Page - First Access">
<div style="page-break-before: always;"></div>
### 1.4 Inloggen als Admin

Administratieve functies zijn beveiligd met een PIN. De standaard-PIN is **0000**.

1. Klik op **🔒 Admin** in de Admin-sectie
2. Voer de PIN in (standaard: `0000`)
3. Klik op **Bevestigen**

U bent nu ingelogd als Admin (weergegeven als 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Admin Login">

> **Beveiligingsaanbeveling:** Wijzig de standaard-PIN direct na de eerste aanmelding (zie sectie 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Uw eerste gebouw aanmaken

Een «gebouw» in de Stagebox vertegenwoordigt een project of installatielocatie. Elk gebouw heeft zijn eigen apparatendatabase, IP-pool en configuratie.

1. Zorg dat u bent ingelogd als Admin (🔓 Admin zichtbaar)
2. Klik op **➕ Nieuw gebouw**
3. Voer een gebouwnaam in (bijv. `klant_woning`)
   - Gebruik alleen kleine letters, cijfers en underscores
   - Spaties en speciale tekens worden automatisch geconverteerd
4. Klik op **Aanmaken**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="New Building Dialog">

Het gebouw wordt aangemaakt en **opent automatisch** met het WiFi-configuratiedialoog.

---

> ⚠️ **KRITIEK: Configureer de WiFi-instellingen correct!**
>
> De WiFi-instellingen die u hier invoert bepalen met welk netwerk uw Shelly-apparaten verbinding maken. **Onjuiste instellingen maken apparaten onbereikbaar!**
>
> - Controleer de SSID-spelling (hoofdlettergevoelig!)
> - Controleer of het wachtwoord correct is
> - Zorg dat de IP-bereiken overeenkomen met uw werkelijke netwerk
>
> Apparaten die met verkeerde WiFi-gegevens zijn geprovisioneerd, moeten worden gereset en opnieuw geprovisioneerd.

<div style="page-break-before: always;"></div>

### 1.6 WiFi en IP-bereiken configureren

Na het aanmaken van een gebouw verschijnt automatisch het dialoog **Gebouwinstellingen**.

<img src="screenshots/07-building-settings.png" width="200" alt="Building Settings">

#### WiFi-configuratie

Voer de WiFi-gegevens in waarmee de Shelly-apparaten verbinding moeten maken:

**Primair WiFi (vereist):**
- SSID: Uw netwerknaam (bijv. `HomeNetwork`)
- Wachtwoord: Uw WiFi-wachtwoord

**Uitwijk-WiFi (optioneel):**
- Een back-upnetwerk als het primaire niet beschikbaar is

<img src="screenshots/08-wifi-settings.png" width="450" alt="WiFi Settings">

#### IP-adresbereiken

Configureer de statische IP-pool voor Shelly-apparaten:

**Shelly Pool:**
- Van: Eerste IP voor apparaten (bijv. `192.168.1.50`)
- Tot: Laatste IP voor apparaten (bijv. `192.168.1.99`)

**Gateway:**
- Meestal het IP van uw router (bijv. `192.168.1.1`)
- Leeg laten voor automatische detectie (.1)

**DHCP-scanbereik (optioneel):**
- Bereik waar nieuwe apparaten verschijnen na een fabrieksreset
- Leeg laten om het hele subnet te scannen (langzamer)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="IP Range Settings">

> **Waarschuwing:** De IP-bereiken moeten overeenkomen met uw werkelijke netwerk! Apparaten zijn onbereikbaar als ze met een verkeerd subnet worden geconfigureerd.

5. Klik op **💾 Opslaan**

<div style="page-break-before: always;"></div>

### 1.7 Admin-PIN wijzigen

Om uw Admin-PIN te wijzigen (standaard is `0000`):

1. Klik op **🔓 Admin** (moet ingelogd zijn)
2. Klik op **🔑 PIN wijzigen**
3. Voer de nieuwe PIN in (minimaal 4 cijfers)
4. Bevestig de nieuwe PIN
5. Klik op **Opslaan**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="Change PIN Dialog">

> **Belangrijk:** Onthoud deze PIN! Deze beveiligt alle administratieve functies, inclusief het verwijderen van gebouwen en systeeminstellingen.

### 1.8 Volgende stappen

Uw Stagebox is nu klaar voor het provisioneren van apparaten. Ga verder met Deel 2 voor meer informatie over:
- Provisioneren van nieuwe Shelly-apparaten (Stage 1–4)
- Apparaatbeheer
- Back-ups maken

---

<div style="page-break-before: always;"></div>

## Deel 2: Functiereferentie

### 2.1 Welkomstpagina (Gebouwselectie)

De welkomstpagina is het startpunt na toegang tot de Stagebox. Het toont alle gebouwen en biedt systeembrede functies.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Greeting Page Overview">

#### 2.1.1 Gebouwenlijst

Het middengebied toont alle beschikbare gebouwen als kaarten.

Elke gebouwkaart toont:
- Gebouwnaam
- IP-bereik-samenvatting
- Aantal apparaten

**Acties (alleen Admin-modus):**
- ✏️ Gebouw hernoemen
- 🗑️ Gebouw verwijderen

<img src="screenshots/21-building-cards.png" width="200" alt="Building Cards">

**Een gebouw selecteren:**
- Enkele klik om te selecteren
- Dubbelklik om direct te openen
- Klik op **Openen →** na selectie

#### 2.1.2 Systeemsectie

Links van de gebouwenlijst:

| Knop | Functie | Admin vereist |
|------|---------|---------------|
| 💾 Back-up naar USB | Back-up van alle gebouwen op USB-stick maken | Nee |
| 🔄 Herstarten | Stagebox herstarten | Nee |
| ⏻ Afsluiten | Stagebox veilig afsluiten | Nee |

> **Belangrijk:** Gebruik altijd **Afsluiten** voordat u de voeding loskoppelt om gegevensverlies te voorkomen.

#### 2.1.3 Admin-sectie

Administratieve functies (vereist Admin-PIN):

| Knop | Functie |
|------|---------|
| 🔒/🔓 Admin | Inloggen/Uitloggen |
| ➕ Nieuw gebouw | Een nieuw gebouw aanmaken |
| 📤 Alle gebouwen exporteren | ZIP van alle gebouwen downloaden |
| 📥 Gebouw(en) importeren | Importeren vanuit ZIP-bestand |
| 📜 Shelly Script Pool | Gedeelde scripts beheren |
| 📂 Herstellen van USB | Gebouwen herstellen vanuit USB-back-up |
| 🔌 USB-stick formatteren | USB voorbereiden voor back-ups |
| 🔑 PIN wijzigen | Admin-PIN wijzigen |
| 📦 Stagebox Update | Controleren op software-updates |
| 🖥️ Systeemupdates | Controleren op OS-updates |
| 🌐 Taal | Taal van de interface wijzigen |
| 🏢 Installatieprofiel | Bedrijfsinformatie voor rapporten configureren |


#### 2.1.4 USB-back-up

**Een back-up maken:**

1. Steek een USB-stick in (elk formaat)
2. Indien niet geformatteerd voor Stagebox: Klik op **🔌 USB-stick formatteren** (Admin)
3. Klik op **💾 Back-up naar USB**
4. Wacht op het voltooiingsbericht
5. De USB-stick kan nu veilig worden verwijderd

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="USB Format Dialog">

**Herstellen van USB:**

1. Steek de USB-stick met back-ups in
2. Klik op **📂 Herstellen van USB** (Admin)
3. Selecteer een back-up uit de lijst
4. Kies de te herstellen gebouwen
5. Klik op **Geselecteerde herstellen**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="USB Restore Dialog">

#### 2.1.5 Gebouwen exporteren/importeren

**Export:**
1. Klik op **📤 Alle gebouwen exporteren** (Admin)
2. Een ZIP-bestand met alle gebouwgegevens wordt gedownload

**Import:**
1. Klik op **📥 Gebouw(en) importeren** (Admin)
2. Sleep een ZIP-bestand of klik om te selecteren
3. Kies de te importeren gebouwen
4. Selecteer de actie voor bestaande gebouwen (overslaan/overschrijven)
5. Klik op **Geselecteerde importeren**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Import Buildings Dialog">

<div style="page-break-before: always;"></div>

### 2.2 Gebouwpagina

De gebouwpagina is de hoofdwerkruimte voor het provisioneren en beheren van apparaten in een specifiek gebouw.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Building Page Overview">

#### Layout:
- **Linker zijbalk:** Provisioneringsfasen, filters, acties, instellingen
- **Middengebied:** Apparatenlijst
- **Rechter zijbalk:** Stage-panelen of apparaatdetails, Script-, KVS-, Webhook-, Planning- en OTA-tabbladen

### 2.3 Linker zijbalk

#### 2.3.1 Gebouwkop

Toont de huidige gebouwnaam. Klik om terug te keren naar de welkomstpagina.
<div style="page-break-before: always;"></div>

#### 2.3.2 Provisioneringsfasen

De 4-fasen provisioneringspijplijn:

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Provisioning Stages">

**S1 — AP-provisionering:**
- Zoekt naar Shelly-apparaten in AP-modus (Access Point)
- Configureert WiFi-gegevens
- Schakelt cloud, BLE en AP-modus uit

**S2 — Adoptie:**
- Scant het netwerk op nieuwe apparaten (DHCP-bereik)
- Wijst statische IP's toe uit de pool
- Registreert apparaten in de database

**S3 — OTA & Namen:**
- Werkt firmware bij naar de nieuwste versie
- Synchroniseert beschrijvende namen naar apparaten

**S4 — Configuratie:**
- Past apparaatprofielen toe
- Configureert ingangen, schakelaars, rolluiken, enz.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1: AP-provisionering

1. Klik op de knop **S1**
2. De Stagebox WiFi-adapter zoekt naar Shelly-AP's
3. Gevonden apparaten worden automatisch geconfigureerd, de apparatenteller telt op
4. Klik op **⏹ Stop** wanneer gereed

<img src="screenshots/32-stage1-panel.png" width="450" alt="Stage 1 Panel">

> **Tip:** Zet Shelly-apparaten in AP-modus door de knop 10+ seconden ingedrukt te houden of een fabrieksreset uit te voeren.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2: Adoptie

1. Klik op de knop **S2**
2. Klik op **Netwerk scannen**
3. Nieuwe apparaten verschijnen in de lijst
4. Selecteer apparaten om te adopteren of klik op **Alles adopteren**
5. Apparaten ontvangen statische IP's en worden geregistreerd

<img src="screenshots/33-stage2-panel.png" width="300" alt="Stage 2 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3: OTA & Namen

1. Klik op de knop **S3**
2. Apparaten in Stage 2 worden weergegeven
3. Klik op **Stage 3 uitvoeren** om:
   - Firmware bij te werken (indien nieuwere beschikbaar)
   - Beschrijvende namen van de database naar apparaten te synchroniseren

<img src="screenshots/34-stage3-panel.png" width="300" alt="Stage 3 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4: Configuratie

1. Klik op de knop **S4**
2. Apparaten in Stage 3 worden weergegeven
3. Klik op **Stage 4 uitvoeren** om profielen toe te passen:
   - Schakelaarinstellingen (initiële status, auto-uit)
   - Rolluikinstellingen (richting omwisselen, limieten)
   - Ingangsconfiguraties
   - Aangepaste acties

<img src="screenshots/35-stage4-panel.png" width="300" alt="Stage 4 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filters

Filter de apparatenlijst op verschillende criteria:

| Filter | Beschrijving |
|--------|-------------|
| Stage | Apparaten in een specifieke provisioneringsfase tonen |
| Kamer | Apparaten in een specifieke kamer tonen |
| Model | Specifieke apparaattypen tonen |
| Status | Online-/offline-apparaten |

<img src="screenshots/36-filter-panel.png" width="200" alt="Filter Panel">

#### 2.3.8 Acties

Bulkbewerkingen op geselecteerde apparaten:

| Actie | Beschrijving |
|-------|-------------|
| 🔄 Vernieuwen | Apparaatstatus bijwerken |
| 📋 Kopiëren | Apparaatinfo naar klembord kopiëren |
| 📤 CSV exporteren | Geselecteerde apparaten exporteren |
| 🗑️ Verwijderen | Uit database verwijderen (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Apparatenlijst

Het middengebied toont alle apparaten in het huidige gebouw.

<img src="screenshots/40-device-list.png" width="500" alt="Device List">

#### Kolommen:

| Kolom | Beschrijving |
|-------|-------------|
| ☑️ | Selectievakje |
| Status | Online (🟢) / Offline (🔴) |
| Naam | Beschrijvende naam van het apparaat |
| Kamer | Toegewezen kamer |
| Locatie | Positie binnen de kamer |
| Model | Apparaattype |
| IP | Huidig IP-adres |
| Stage | Huidige provisioneringsfase (S1–S4) |

#### Selectie:
- Klik op het vakje om individuele apparaten te selecteren
- Klik op het kopvakje om alle zichtbare te selecteren
- Shift+klik voor bereikselectie

#### Sortering:
- Klik op de kolomkop om te sorteren
- Klik opnieuw om de volgorde om te keren

<div style="page-break-before: always;"></div>

### 2.5 Rechter zijbalk (Apparaatdetails)

Wanneer een apparaat is geselecteerd, toont de rechter zijbalk gedetailleerde informatie en acties.

#### 2.5.1 Tabblad Apparaatinfo

Basisinformatie over het apparaat:

| Veld | Beschrijving |
|------|-------------|
| Naam | Bewerkbare beschrijvende naam |
| Kamer | Kamertoewijzing (bewerkbaar) |
| Locatie | Positie binnen de kamer (bewerkbaar) |
| MAC | Hardwareadres |
| IP | Netwerkadres |
| Model | Hardwaremodel |
| Firmware | Huidige versie |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Device Info Tab">

<div style="page-break-before: always;"></div>

#### 2.5.2 Tabblad Scripts

Scripts op het geselecteerde apparaat beheren:

- Geïnstalleerde scripts bekijken
- Scripts starten/stoppen
- Scripts verwijderen
- Nieuwe scripts uitrollen

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Device Scripts Tab">

#### 2.5.3 Tabblad KVS

Key-Value Store-vermeldingen bekijken en bewerken:

- Systeemwaarden (alleen-lezen)
- Gebruikerswaarden (bewerkbaar)
- Nieuwe vermeldingen toevoegen
- Vermeldingen verwijderen

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Device KVS Tab">
<div style="page-break-before: always;"></div>

#### 2.5.4 Tabblad Webhooks

Apparaat-webhooks configureren:

- Bestaande webhooks bekijken
- Nieuwe webhooks toevoegen
- URL's en voorwaarden bewerken
- Webhooks verwijderen

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Device Webhooks Tab">
<div style="page-break-before: always;"></div>

#### 2.5.5 Tabblad Planningen

Het tabblad Planningen stelt u in staat om tijdgebaseerde automatiseringen te maken, beheren en uit te rollen naar Shelly-apparaten. Planningen worden opgeslagen als sjablonen en kunnen tegelijkertijd naar meerdere compatibele apparaten worden uitgerold.

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Device Schedules Tab">

**Overzicht van het tabblad:**

Het tabblad Planningen is onderverdeeld in drie gebieden:

1. **Sjablonenlijst** — opgeslagen planningssjablonen met bewerkings-/verwijderbediening
2. **Doelapparaten** — lijst met selectievakjes om uitroldoelen te selecteren
3. **Actieknoppen** — Uitrollen, Status en Alles verwijderen

##### Een planning aanmaken

1. Klik op **+ Nieuw** om de planningseditor te openen
2. Voer een **Naam** en een optionele **Beschrijving** in

<img src="screenshots/54a-schedule-editor-modal.png" width="500" alt="Schedule Editor Modal">

**Linkerkolom — Tijdinstelling:**

Selecteer een van de vier tijdinstellingsmodi:

| Modus | Beschrijving |
|-------|-------------|
| 🕐 **Tijd** | Een specifiek tijdstip van de dag instellen (uren en minuten) |
| 🌅 **Zonsopgang** | Activering bij zonsopgang, met optionele offset |
| 🌇 **Zonsondergang** | Activering bij zonsondergang, met optionele offset |
| 📅 **Interval** | Herhaling op regelmatige intervallen — kies uit voorinstellingen (elke 5 min, 15 min, 30 min, elk uur, elke 2 uur) of voer aangepaste minuten-/uurwaarden in |

Onder de tijdinstellingsmodus selecteert u de **weekdagen** met selectievakjes (ma–zo).

Het **timespec**-veld toont de gegenereerde Shelly cron-expressie (alleen-lezen). Eronder wordt een voorbeeld van de volgende geplande uitvoeringstijden weergegeven.

Het selectievakje **Ingeschakeld** bepaalt of de planning actief is na uitrol.

**Rechterkolom — Acties:**

3. Selecteer een **Referentieapparaat** uit het keuzemenu — Stagebox bevraagt dit apparaat om de beschikbare componenten en acties te bepalen (bijv. Switch, Cover, Light)
4. Voeg een of meer **Acties** toe (maximaal 5 per planning) door op **+ Actie toevoegen** te klikken:
   - De beschikbare methoden hangen af van de componenten van het referentieapparaat
   - Voorbeelden: `Switch.Set` (aan/uit), `Cover.GoToPosition` (0–100), `Light.Set` (aan/uit/helderheid)
   - Verwijder een actie met de knop **✕**

5. Klik op **💾 Opslaan** om het sjabloon op te slaan, of **Annuleren** om te verwerpen

> **Tip:** Het referentieapparaat bepaalt welke acties beschikbaar zijn. Kies een apparaat dat de componenten heeft die u wilt aansturen.

##### Een planning bewerken

- Klik op de knop **✏️ Bewerken** naast een sjabloon, of **dubbelklik** op de sjabloonnaam
- De planningseditor opent vooraf ingevuld met de bestaande instellingen
- Wijzig en klik op **💾 Opslaan**

##### Planningen uitrollen

1. Selecteer een planningssjabloon uit de lijst
2. Vink de doelapparaten aan in de sectie **Doelapparaten**
   - Gebruik **Alles selecteren** / **Geen** voor snelle selectie
   - Incompatibele apparaten (ontbrekende vereiste componenten) worden automatisch overgeslagen tijdens de uitrol
3. Klik op **📤 Uitrollen**
4. De resultaten worden per apparaat getoond met succes-/faalstatus

> **Opmerking:** Vóór de uitrol controleert Stagebox elk doelapparaat op de vereiste componenten. Apparaten die de benodigde componenten missen (bijv. een Cover-planning uitrollen naar een apparaat met alleen een Switch) worden overgeslagen met een foutmelding.

##### Planningstatus controleren

1. Selecteer de doelapparaten
2. Klik op **📋 Status**
3. Stagebox bevraagt elk apparaat en toont de momenteel geïnstalleerde planningen, inclusief timespec, methode en ingeschakeld/uitgeschakeld-status

##### Planningen van apparaten verwijderen

1. Selecteer de doelapparaten
2. Klik op **🗑️ Alles verwijderen**
3. Alle planningen op de geselecteerde apparaten worden verwijderd

> **Waarschuwing:** «Alles verwijderen» verwijdert **alle** planningen van de geselecteerde apparaten, niet alleen de door Stagebox uitgerolde planningen.

<img src="screenshots/54b-schedule-tab-overview.png" width="300" alt="Schedule Tab Overview">
<div style="page-break-before: always;"></div>

#### 2.5.6 Tabblad Virtuele componenten

Virtuele componenten op apparaten configureren:

- Virtuele schakelaars
- Virtuele sensoren
- Tekstcomponenten
- Nummercomponenten

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Device Virtuals Tab">

#### 2.5.7 Tabblad FW-updates

Apparaatfirmware beheren:

- Huidige versie bekijken
- Controleren op updates
- Firmware-updates toepassen

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Device FW-Updates Tab">
<div style="page-break-before: always;"></div>

### 2.6 Scriptbeheer

#### 2.6.1 Script Pool (Admin)

Gedeelde scripts voor uitrol beheren:

1. Ga naar de welkomstpagina
2. Klik op **📜 Shelly Script Pool** (Admin)
3. JavaScript-bestanden (.js) uploaden
4. Ongebruikte scripts verwijderen

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Script Pool Dialog">
<div style="page-break-before: always;"></div>

#### 2.6.2 Scripts uitrollen

1. Selecteer het/de doelapparatat(en) in de apparatenlijst
2. Ga naar het tabblad **Scripts**
3. Selecteer de bron: **Lokaal** (Script Pool) of **GitHub-bibliotheek**
4. Kies een script
5. Configureer de opties:
   - ☑️ Uitvoeren bij opstarten
   - ☑️ Starten na uitrol
6. Klik op **📤 Uitrollen**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Deploy Script Dialog">

<div style="page-break-before: always;"></div>

### 2.7 Expertinstellingen (Geavanceerd)

> ⚠️ **Waarschuwing:** De expertinstellingen bieden directe configuratie van het provisioneringsgedrag en systeemparameters. Onjuiste wijzigingen kunnen de apparaatprovisionering beïnvloeden. Gebruik met voorzichtigheid!

Toegang via de sectie **Expert** → **⚙️ Gebouwinstellingen** in de zijbalk van de gebouwpagina.

Het dialoog Gebouwinstellingen biedt een interface met tabbladen voor het configureren van geavanceerde opties.

---

#### 2.7.1 Tabblad Provisionering

Regelt het gedrag van de Stage 1 (AP-modus) provisionering.

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Expert Provisioning Tab">

| Instelling | Beschrijving | Standaard |
|------------|-------------|-----------|
| **Lusmodus** | Continu zoeken naar nieuwe apparaten. Wanneer ingeschakeld, blijft Stage 1 na elke succesvolle provisionering zoeken naar nieuwe Shelly-AP's. Uitschakelen voor provisionering van één apparaat. | ☑️ Aan |
| **AP uitschakelen na provisionering** | WiFi-Access Point van het apparaat uitschakelen nadat het verbinding heeft gemaakt met uw netwerk. Aanbevolen voor beveiliging. | ☑️ Aan |
| **Bluetooth uitschakelen** | Bluetooth uitschakelen op geprovisioneerde apparaten. Bespaart stroom en verkleint het aanvalsoppervlak. | ☑️ Aan |
| **Cloud uitschakelen** | Shelly Cloud-connectiviteit uitschakelen. Apparaten zijn alleen lokaal bereikbaar. | ☑️ Aan |
| **MQTT uitschakelen** | MQTT-protocol uitschakelen op apparaten. Inschakelen als u een domoticasysteem met MQTT gebruikt. | ☑️ Aan |

---

#### 2.7.2 Tabblad OTA & Namen

Firmware-updategedrag en naamafhandeling configureren tijdens Stage 3.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Expert OTA & Names Tab">

**Firmware-updates (OTA):**

| Instelling | Beschrijving | Standaard |
|------------|-------------|-----------|
| **OTA-updates inschakelen** | Tijdens Stage 3 controleren op firmware-updates en optioneel installeren. | ☑️ Aan |
| **Updatemodus** | `Alleen controleren`: Beschikbare updates melden zonder te installeren. `Controleren & updaten`: Beschikbare updates automatisch installeren. | Alleen controleren |
| **Timeout (seconden)** | Maximale wachttijd voor OTA-bewerkingen. Verhogen voor trage netwerken. | 20 |

**Beschrijvende namen:**

| Instelling | Beschrijving | Standaard |
|------------|-------------|-----------|
| **Beschrijvende namen inschakelen** | Kamer-/locatienamen toepassen op apparaten tijdens Stage 3. Namen worden opgeslagen in de apparaatconfiguratie. | ☑️ Aan |
| **Ontbrekende namen aanvullen** | Automatisch namen genereren voor apparaten die er geen toegewezen hebben. Gebruikt het patroon `<Model>_<MAC-suffix>`. | ☐ Uit |

<div style="page-break-before: always;"></div>

#### 2.7.3 Tabblad Export

CSV-exportinstellingen voor apparaatlabels en rapporten configureren.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Expert Export Tab">

**CSV-scheidingsteken:**

Kies het kolomscheidingsteken voor geëxporteerde CSV-bestanden:
- **Puntkomma (;)** — Standaard, werkt met Europese Excel-versies
- **Komma (,)** — Standaard CSV-formaat
- **Tab** — Voor tabgescheiden waarden

**Standaardkolommen:**

Selecteer welke kolommen in geëxporteerde CSV-bestanden verschijnen. Beschikbare kolommen:

| Kolom | Beschrijving |
|-------|-------------|
| `id` | Apparaat-MAC-adres (unieke identificatie) |
| `ip` | Huidig IP-adres |
| `hostname` | Apparaat-hostnaam |
| `fw` | Firmwareversie |
| `model` | Beschrijvende modelnaam |
| `hw_model` | Hardware-model-ID |
| `friendly_name` | Toegewezen apparaatnaam |
| `room` | Kamertoewijzing |
| `location` | Locatie binnen de kamer |
| `assigned_at` | Tijdstip van provisionering |
| `last_seen` | Laatste communicatietijdstempel |
| `stage3_friendly_status` | Naamtoewijzingsstatus |
| `stage3_ota_status` | Firmware-updatestatus |
| `stage4_status_result` | Resultaat van de configuratiefase |

<div style="page-break-before: always;"></div>

#### 2.7.4 Tabblad Modelkaart

Aangepaste weergavenamen definiëren voor Shelly hardware-model-ID's.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Expert Model Map Tab">

De modelkaart vertaalt interne hardware-identificaties (bijv. `SNSW-001X16EU`) naar leesbare namen (bijv. `Shelly Plus 1`).

**Gebruik:**
1. Voer de **Hardware-ID** exact in zoals gemeld door het apparaat
2. Voer uw gewenste **Weergavenaam** in
3. Klik op **+ Model toevoegen** om meer vermeldingen toe te voegen
4. Klik op **🗑️** om een vermelding te verwijderen

> **Tip:** Controleer de webinterface of API-respons van het apparaat om de exacte hardware-ID-tekenreeks te vinden.

<div style="page-break-before: always;"></div>

#### 2.7.5 Tabblad Geavanceerd (YAML-editor)

Directe bewerking van configuratiebestanden voor geavanceerde scenario's.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Expert Advanced Tab">

**Beschikbare bestanden:**

| Bestand | Beschrijving |
|---------|-------------|
| `config.yaml` | Hoofdconfiguratie van het gebouw (IP-bereiken, apparatendatabase, provisioneringsinstellingen) |
| `profiles/*.yaml` | Apparaatconfiguratieprofielen voor Stage 4 |

**Functies:**
- Syntaxvalidatie (groene/rode indicator)
- Bestandsselectie uit het keuzemenu
- Directe inhoudsbewerking
- Alle wijzigingen worden automatisch opgeslagen vóór het bewaren

**Validatie-indicator:**
- 🟢 Groen: Geldige YAML-syntaxis
- 🔴 Rood: Syntaxfout (details bij hoveren)

> **Aanbeveling:** Gebruik de andere tabbladen voor normale configuratie. Gebruik de YAML-editor alleen wanneer u instellingen moet wijzigen die niet beschikbaar zijn in de UI, of voor probleemoplossing.

<div style="page-break-before: always;"></div>

### 2.8 Systeemonderhoud

#### 2.8.1 Stagebox-updates

Stagebox-software-updates controleren en installeren:

1. Ga naar de welkomstpagina
2. Klik op **📦 Stagebox Update** (Admin)
3. De huidige en beschikbare versies worden getoond
4. Klik op **⬇️ Update installeren** indien beschikbaar
5. Wacht op de installatie en automatische herstart

<img src="screenshots/80-stagebox-update.png" width="450" alt="Stagebox Update Dialog">
<div style="page-break-before: always;"></div>

#### 2.8.2 Systeemupdates

Besturingssysteemupdates controleren en installeren:

1. Ga naar de welkomstpagina
2. Klik op **🖥️ Systeemupdates** (Admin)
3. Beveiligings- en systeemupdates worden weergegeven
4. Klik op **⬇️ Updates installeren**
5. Het systeem kan herstarten indien nodig

<img src="screenshots/81-system-updates.png" width="450" alt="System Updates Dialog">

---

<div style="page-break-before: always;"></div>

### 2.9 Rapporten & Documentatie

Stagebox biedt uitgebreide rapportagefuncties voor professionele installatiedocumentatie. Rapporten bevatten apparaatinventarissen, configuratiedetails en kunnen worden aangepast met installateurbranding.

#### 2.9.1 Installatieprofiel

Het installatieprofiel bevat uw bedrijfsinformatie die op alle gegenereerde rapporten verschijnt. Dit is een globale instelling die voor alle gebouwen geldt.

**Toegang tot het installatieprofiel:**

1. Ga naar de welkomstpagina
2. Klik op **🏢 Installatieprofiel** (Admin vereist)

**Beschikbare velden:**

| Veld | Beschrijving |
|------|-------------|
| Bedrijfsnaam | Uw bedrijfs- of handelsnaam |
| Adres | Postadres (meerdere regels mogelijk) |
| Telefoon | Contacttelefoonnummer |
| E-mail | Contact-e-mailadres |
| Website | Bedrijfswebsite-URL |
| Logo | Bedrijfslogo-afbeelding (PNG, JPG, max 2 MB) |

**Logorichtlijnen:**
- Aanbevolen formaat: 400×200 pixels of vergelijkbare beeldverhouding
- Formaten: PNG (transparante achtergrond aanbevolen) of JPG
- Maximale bestandsgrootte: 2 MB
- Het logo verschijnt in de koptekst van PDF-rapporten

> **Tip:** Vul het installatieprofiel in voordat u uw eerste rapport genereert om professionele documentatie te garanderen.

<img src="screenshots/90-installer-profile.png" width="450" alt="Installer Profile Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.2 Gebouwprofiel (Objectinformatie)

Elk gebouw kan een eigen profiel hebben met klant- en projectspecifieke informatie. Deze gegevens verschijnen in rapporten die voor dat gebouw worden gegenereerd.

**Toegang tot het gebouwprofiel:**

1. Open de gebouwpagina
2. Ga naar de sectie **Expert** in de zijbalk
3. Klik op **⚙️ Gebouwinstellingen**
4. Selecteer het tabblad **Object**

**Beschikbare velden:**

| Veld | Beschrijving |
|------|-------------|
| Objectnaam | Project- of vastgoednaam (bijv. «Villa Müller») |
| Klantnaam | Naam van de klant |
| Adres | Adres van het vastgoed (meerdere regels mogelijk) |
| Contacttelefoon | Telefoonnummer van de klant |
| Contact-e-mail | E-mailadres van de klant |
| Opmerkingen | Aanvullende notities (verschijnen in rapporten) |

> **Opmerking:** De objectnaam wordt als rapporttitel gebruikt. Als deze niet is ingesteld, wordt in plaats daarvan de gebouwnaam gebruikt.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Building Profile Tab">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Een snapshot legt de volledige status vast van alle apparaten in een gebouw op een specifiek moment. Snapshots worden opgeslagen als ZIP-pakketten met apparaatgegevens en configuratiebestanden.

**Een snapshot maken:**

1. Open de gebouwpagina
2. Ga naar de sectie **Audit** in de zijbalk
3. Klik op **📸 Snapshots**
4. Wacht tot de scan is voltooid

**Snapshotbeheer:**

| Actie | Beschrijving |
|-------|-------------|
| 📥 Downloaden | Snapshot-ZIP-pakket downloaden |
| 🗑️ Verwijderen | Snapshot verwijderen |

**Snapshot-ZIP-inhoud:**

Elke snapshot wordt opgeslagen als een ZIP-bestand met:

| Bestand | Beschrijving |
|---------|-------------|
| `snapshot.json` | Volledige apparaatscangegevens (IP, MAC, config, status) |
| `installer_profile.json` | Bedrijfsinformatie van de installateur |
| `installer_logo.png` | Bedrijfslogo (indien geconfigureerd) |
| `ip_state.json` | Apparatendatabase met kamer-/locatietoewijzingen |
| `building_profile.json` | Object-/klantinformatie |
| `config.yaml` | Gebouwconfiguratie |
| `shelly_model_map.yaml` | Aangepaste modelnaamtoewijzingen (indien geconfigureerd) |
| `scripts/*.js` | Uitgerolde scripts (indien aanwezig) |

> **Tip:** Snapshots zijn zelfstandige pakketten die kunnen worden gebruikt met externe documentatietools of gearchiveerd voor toekomstige referentie.

**Automatische opschoning:**

Stagebox bewaart automatisch alleen de 5 meest recente snapshots per gebouw om opslagruimte te besparen.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Snapshots Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.4 Rapportgenerator

Professionele installatierapporten genereren in PDF- of Excel-formaat.

**Een rapport genereren:**

1. Open de gebouwpagina
2. Ga naar de sectie **Audit** in de zijbalk
3. Klik op **📊 Rapportgenerator**
4. Rapportopties configureren:
   - **Snapshot**: Nieuwe maken of bestaande snapshot selecteren
   - **Taal**: Rapporttaal (DE, EN, FR, IT, NL)
   - **Formaat**: PDF of Excel (XLSX)
5. Klik op **Genereren**

<img src="screenshots/93-report-generator.png" width="450" alt="Report Generator Dialog">

**PDF-rapportinhoud:**

Het PDF-rapport bevat:
- **Koptekst**: Bedrijfslogo, rapporttitel, aanmaakdatum
- **Objectinformatie**: Klantnaam, adres, contactgegevens
- **Samenvatting**: Totaal aantal apparaten, kamers en apparaattypen
- **Apparatentabel**: Volledig inventaris met QR-codes

**Kolommen apparatentabel:**

| Kolom | Beschrijving |
|-------|-------------|
| QR | QR-code met link naar de webinterface van het apparaat |
| Kamer | Toegewezen kamer |
| Locatie | Positie binnen de kamer |
| Naam | Beschrijvende naam van het apparaat |
| Model | Apparaattype |
| IP | Netwerkadres |
| FW | Firmwareversie |
| MAC | Laatste 6 tekens van het MAC-adres |
| SWTAK | Functie-indicatoren (zie hieronder) |

**Functie-indicatoren (SWTAK):**

Elk apparaat toont welke functies zijn geconfigureerd:

| Indicator | Betekenis | Bron |
|-----------|-----------|------|
| **S** | Scripts | Apparaat heeft scripts geïnstalleerd |
| **W** | Webhooks | Apparaat heeft webhooks geconfigureerd |
| **T** | Timers | Auto-aan of auto-uit timers actief |
| **A** | Schedules | Geplande automatiseringen geconfigureerd |
| **K** | KVS | Key-Value Store-vermeldingen aanwezig |

Actieve indicatoren zijn gemarkeerd, inactieve indicatoren zijn grijs.

**Excel-rapport:**

De Excel-export bevat dezelfde informatie als het PDF-rapport in spreadsheetformaat:
- Enkel werkblad met alle apparaten
- Koptekst met rapportmetagegevens
- Legenda ter verklaring van de SWTAK-indicatoren
- Kolommen geoptimaliseerd voor filteren en sorteren

> **Tip:** Gebruik het Excel-formaat wanneer u de gegevens verder wilt verwerken of aangepaste documentatie wilt maken.

<div style="page-break-before: always;"></div>

#### 2.9.5 Configuratie-audit

De auditfunctie vergelijkt de huidige livestatus van alle apparaten met een referentiesnapshot om configuratiewijzigingen, nieuwe apparaten of offline-apparaten te detecteren.

**Een audit uitvoeren:**

1. Open de gebouwpagina
2. Ga naar de sectie **Audit** in de zijbalk
3. Klik op **🔍 Audit starten**
4. Selecteer een referentiesnapshot uit het keuzemenu
5. Klik op **🔍 Audit starten**

<img src="screenshots/94-audit-setup.png" width="450" alt="Audit Setup Dialog">

Het systeem voert een nieuwe scan uit van alle apparaten en vergelijkt deze met de geselecteerde snapshot.

**Auditresultaten:**

| Status | Icoon | Beschrijving |
|--------|-------|-------------|
| OK | ✅ | Apparaat ongewijzigd sinds snapshot |
| Gewijzigd | ⚠️ | Configuratieverschillen gedetecteerd |
| Offline | ❌ | Apparaat was in snapshot maar reageert niet |
| Nieuw | 🆕 | Apparaat gevonden dat niet in snapshot was |

<img src="screenshots/95-audit-results.png" width="500" alt="Audit Results">

**Gedetecteerde wijzigingen:**

De audit detecteert en rapporteert:
- IP-adreswijzigingen
- Naamwijzigingen van apparaten
- Firmware-updates
- Configuratiewijzigingen (ingangstypen, schakelaarinstellingen, rolluikinstellingen)
- WiFi-instellingswijzigingen
- Nieuwe of ontbrekende apparaten

**Toepassingen:**

- **Verificatie na installatie**: Bevestigen dat alle apparaten zijn geconfigureerd zoals gedocumenteerd
- **Onderhoudscontroles**: Onverwachte wijzigingen sinds het laatste bezoek detecteren
- **Probleemoplossing**: Identificeren welke instellingen zijn gewijzigd
- **Opleverdocumentatie**: Controleren of de installatie overeenkomt met de specificatie vóór oplevering

> **Tip:** Maak een snapshot na het voltooien van een installatie om te gebruiken als referentie voor toekomstige audits.

<div style="page-break-before: always;"></div>

## Bijlage

### A. Sneltoetsen

| Sneltoets | Actie |
|-----------|-------|
| `Escape` | Dialoog/modaal sluiten |
| `Enter` | Dialoog bevestigen |

### B. Statusindicatoren

| Icoon | Betekenis |
|-------|-----------|
| 🟢 (groen) | Apparaat online |
| 🔴 (rood) | Apparaat offline |
| S1–S4 | Huidige provisioneringsfase |
| ⚡ | Firmware-update beschikbaar |

### C. Probleemoplossing

**Kan geen toegang krijgen tot de Web-UI:**
- Controleer de Ethernet-verbinding
- Controleer of de Stagebox een IP heeft (router-DHCP-lijst of OLED-display)
- Probeer het IP-adres direct in plaats van .local

**Admin-PIN vergeten:**
- Houd de OLED-knop **10+ seconden** ingedrukt
- Het display toont «PIN RESET» en «PIN = 0000»
- De PIN is nu gereset naar de standaard `0000`
- Log in met `0000` en wijzig de PIN onmiddellijk

**Apparaten niet gevonden in Stage 1:**
- Zorg dat het apparaat in AP-modus staat (LED knippert)
- Breng de Stagebox dichter bij het apparaat
- Controleer de WiFi-adapterverbinding

**Apparaten niet gevonden in Stage 2:**
- Controleer de DHCP-bereikinstellingen
- Controleer of het apparaat met het juiste WiFi is verbonden
- Wacht 30 seconden na Stage 1

**Stage 4 mislukt:**
- Controleer de apparaatcompatibiliteit
- Controleer of er een profiel bestaat voor het apparaattype
- Controleer of het apparaat online is

**USB-back-upfouten:**
- USB-stick verwijderen en opnieuw inbrengen
- Als de fout aanhoudt, pagina vernieuwen (Ctrl+F5)
- Zorg dat de USB-stick is geformatteerd voor Stagebox (Admin → USB-stick formatteren)

**Trage rapportgeneratie:**
- Grote installaties (50+ apparaten) kunnen 10–20 seconden duren
- PDF-generatie omvat het aanmaken van QR-codes voor elk apparaat
- Gebruik het Excel-formaat voor snellere generatie zonder QR-codes

---

*Stagebox Web-UI Handleiding — Versie 1.1.0*