# Manuale utente Stagebox Web-UI

## Parte 1: Primi passi

Questa guida ti accompagna nella configurazione iniziale della tua Stagebox e nella creazione del tuo primo progetto edificio.
  



<img src="screenshots/01-stagebox-picture.png" width="700" alt="Foto del prodotto">

### 1.1 Collegamento della Stagebox

1. Collega la Stagebox alla tua rete utilizzando un cavo Ethernet
2. Collega l'alimentatore
3. Attendi circa 60 secondi per l'avvio del sistema
4. Il display OLED sul frontale mostrerà le informazioni di connessione

> **Nota:** La Stagebox richiede una connessione di rete cablata. Il WiFi viene utilizzato solo per il provisioning dei dispositivi Shelly.

<div style="page-break-before: always;"></div>

### 1.2 Utilizzo del display OLED

La Stagebox è dotata di un display OLED integrato che alterna automaticamente diverse schermate informative (ogni 10 secondi).

**Schermata 1 - Splash (Identificazione principale):**

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

Questa schermata mostra:
- Titolo "STAGEBOX"
- Indirizzo IP per l'accesso web
- Suffisso MAC (ultimi 6 caratteri per l'identificazione)

**Schermata 2 - Info edificio:**
- Versione attuale della Stagebox
- Nome dell'edificio attivo

**Schermata 3 - Stato del sistema:**
- Temperatura e carico CPU
- Temperatura NVMe
- Utilizzo RAM e disco

**Schermata 4 - Rete:**
- Indirizzo IP Ethernet
- Indirizzo IP WLAN (se connesso)
- Hostname

**Schermata 5 - Orologio:**
- Ora attuale con secondi
- Data attuale

<div style="page-break-before: always;"></div>

**Funzioni del pulsante OLED:**

Il pulsante sul case Argon ONE controlla il display:

| Durata pressione | Azione |
|------------------|--------|
| Pressione breve (<2s) | Passa alla schermata successiva |
| Pressione lunga (2-10s) | Attiva/disattiva display |
| Pressione molto lunga (10s+) | Reimposta PIN Admin a `0000` |

> **Suggerimento:** Usa la schermata Splash o Rete per trovare l'indirizzo IP necessario per accedere all'interfaccia Web.

<div style="page-break-before: always;"></div>

### 1.3 Accesso all'interfaccia Web

Trova l'indirizzo IP sul display OLED (schermata Splash o Rete), quindi apri un browser web e naviga a:

```
http://<INDIRIZZO-IP>:5000
```

Per esempio: `http://192.168.1.100:5000`

**Alternativa usando l'hostname:**

```
http://stagebox-XXXXXX.local:5000
```

Sostituisci `XXXXXX` con il suffisso MAC mostrato sul display OLED.

> **Nota:** L'hostname `.local` richiede il supporto mDNS (Bonjour). Se non funziona, usa direttamente l'indirizzo IP.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Pagina di benvenuto - Primo accesso">
<div style="page-break-before: always;"></div>

### 1.4 Accesso come Admin

Le funzioni amministrative sono protette da un PIN. Il PIN predefinito è **0000**.

1. Clicca su **🔒 Admin** nella sezione Admin
2. Inserisci il PIN (predefinito: `0000`)
3. Clicca su **Conferma**

Ora sei connesso come Admin (mostrato come 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Login Admin">

> **Raccomandazione di sicurezza:** Cambia il PIN predefinito immediatamente dopo il primo accesso (vedi sezione 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Creare il tuo primo edificio

Un "edificio" in Stagebox rappresenta un progetto o un sito di installazione. Ogni edificio ha il proprio database dispositivi, pool IP e configurazione.

1. Assicurati di essere connesso come Admin (🔓 Admin visibile)
2. Clicca su **➕ Nuovo edificio**
3. Inserisci un nome edificio (es: `casa_cliente`)
   - Usa solo lettere minuscole, numeri e underscore
   - Spazi e caratteri speciali vengono convertiti automaticamente
4. Clicca su **Crea**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="Dialogo Nuovo edificio">

L'edificio viene creato e **si apre automaticamente** con il dialogo di configurazione WiFi.

---

> ⚠️ **CRITICO: Configura correttamente le impostazioni WiFi!**
>
> Le impostazioni WiFi che inserisci qui determinano a quale rete si connetteranno i tuoi dispositivi Shelly. **Impostazioni errate renderanno i dispositivi irraggiungibili!**
>
> - Controlla l'ortografia dell'SSID (sensibile alle maiuscole!)
> - Verifica che la password sia corretta
> - Assicurati che i range IP corrispondano alla tua rete reale
>
> I dispositivi provisionati con credenziali WiFi errate devono essere ripristinati alle impostazioni di fabbrica e riprovisionati.

<div style="page-break-before: always;"></div>

### 1.6 Configurazione WiFi e range IP

Dopo aver creato un edificio, appare automaticamente il dialogo **Impostazioni edificio**.

<img src="screenshots/07-building-settings.png" width="200" alt="Impostazioni edificio">

#### Configurazione WiFi

Inserisci le credenziali WiFi a cui i dispositivi Shelly devono connettersi:

**WiFi primario (richiesto):**
- SSID: Nome della tua rete (es: `ReteCasa`)
- Password: La tua password WiFi

**WiFi di backup (opzionale):**
- Una rete di riserva se la primaria non è disponibile

<img src="screenshots/08-wifi-settings.png" width="450" alt="Impostazioni WiFi">

#### Range indirizzi IP

Configura il pool di IP statici per i dispositivi Shelly:

**Pool Shelly:**
- Da: Primo IP per i dispositivi (es: `192.168.1.50`)
- A: Ultimo IP per i dispositivi (es: `192.168.1.99`)

**Gateway:**
- Solitamente l'IP del tuo router (es: `192.168.1.1`)
- Lascia vuoto per il rilevamento automatico (.1)

**Range scansione DHCP (opzionale):**
- Range dove appaiono i nuovi dispositivi dopo il reset di fabbrica
- Lascia vuoto per scansionare l'intera subnet (più lento)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="Impostazioni range IP">

> **Avviso:** I range IP devono corrispondere alla tua rete reale! I dispositivi saranno irraggiungibili se configurati con subnet errata.

5. Clicca su **💾 Salva**

<div style="page-break-before: always;"></div>

### 1.7 Cambiare il PIN Admin

Per cambiare il tuo PIN Admin (predefinito `0000`):

1. Clicca su **🔓 Admin** (devi essere connesso)
2. Clicca su **🔑 Cambia PIN**
3. Inserisci il nuovo PIN (minimo 4 cifre)
4. Conferma il nuovo PIN
5. Clicca su **Salva**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="Dialogo Cambia PIN">

> **Importante:** Ricorda questo PIN! Protegge tutte le funzioni amministrative inclusa l'eliminazione degli edifici e le impostazioni di sistema.

### 1.8 Prossimi passi

La tua Stagebox è ora pronta per il provisioning dei dispositivi. Continua con la Parte 2 per saperne di più su:
- Provisioning di nuovi dispositivi Shelly (Stage 1-4)
- Gestione dei dispositivi
- Creazione di backup

---

<div style="page-break-before: always;"></div>

## Parte 2: Riferimento funzioni

### 2.1 Pagina di benvenuto (Selezione edificio)

La pagina di benvenuto è il punto di partenza dopo l'accesso alla Stagebox. Mostra tutti gli edifici e fornisce funzioni di sistema globali.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Panoramica pagina di benvenuto">

#### 2.1.1 Lista edifici

L'area centrale mostra tutti gli edifici disponibili come schede.

Ogni scheda edificio mostra:
- Nome edificio
- Riepilogo range IP
- Conteggio dispositivi

**Azioni (solo modalità Admin):**
- ✏️ Rinomina edificio
- 🗑️ Elimina edificio

<img src="screenshots/21-building-cards.png" width="200" alt="Schede edifici">

**Selezione di un edificio:**
- Singolo clic per selezionare
- Doppio clic per aprire direttamente
- Clicca **Apri →** dopo la selezione

#### 2.1.2 Sezione Sistema

Situata a sinistra della lista edifici:

| Pulsante | Funzione | Admin richiesto |
|----------|----------|-----------------|
| 💾 Backup su USB | Crea backup di tutti gli edifici su chiavetta USB | No |
| 🔄 Riavvia | Riavvia la Stagebox | No |
| ⏻ Spegni | Spegni la Stagebox in sicurezza | No |

> **Importante:** Usa sempre **Spegni** prima di scollegare l'alimentazione per evitare la corruzione dei dati.

#### 2.1.3 Sezione Admin

Funzioni amministrative (richiede PIN Admin):

| Pulsante | Funzione |
|----------|----------|
| 🔒/🔓 Admin | Login/Logout |
| ➕ Nuovo edificio | Crea un nuovo edificio |
| 📤 Esporta tutti gli edifici | Scarica ZIP di tutti gli edifici |
| 📥 Importa edificio/i | Importa da file ZIP |
| 📜 Pool script Shelly | Gestisci script condivisi |
| 📂 Ripristina da USB | Ripristina edifici da backup USB |
| 🔌 Formatta chiavetta USB | Prepara USB per i backup |
| 🔑 Cambia PIN | Cambia PIN Admin |
| 📦 Aggiornamento Stagebox | Verifica aggiornamenti software |
| 🖥️ Aggiornamenti sistema | Verifica aggiornamenti OS |
| 🌐 Lingua | Cambia lingua interfaccia |
| 🏢 Profilo installatore | Configura informazioni aziendali per i report |


#### 2.1.4 Backup USB

**Creare un backup:**

1. Inserisci una chiavetta USB (qualsiasi formato)
2. Se non formattata per Stagebox: Clicca su **🔌 Formatta chiavetta USB** (Admin)
3. Clicca su **💾 Backup su USB**
4. Attendi il messaggio di completamento
5. La chiavetta USB può ora essere rimossa in sicurezza

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="Dialogo Formatta USB">

**Ripristinare da USB:**

1. Inserisci la chiavetta USB con i backup
2. Clicca su **📂 Ripristina da USB** (Admin)
3. Seleziona un backup dalla lista
4. Scegli gli edifici da ripristinare
5. Clicca su **Ripristina selezionati**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="Dialogo Ripristino USB">

#### 2.1.5 Esporta/Importa edifici

**Esporta:**
1. Clicca su **📤 Esporta tutti gli edifici** (Admin)
2. Viene scaricato un file ZIP contenente tutti i dati degli edifici

**Importa:**
1. Clicca su **📥 Importa edificio/i** (Admin)
2. Trascina un file ZIP o clicca per selezionare
3. Scegli quali edifici importare
4. Seleziona l'azione per gli edifici esistenti (salta/sovrascrivi)
5. Clicca su **Importa selezionati**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Dialogo Importa edifici">

<div style="page-break-before: always;"></div>

### 2.2 Pagina edificio

La pagina edificio è lo spazio di lavoro principale per il provisioning e la gestione dei dispositivi in un edificio specifico.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Panoramica pagina edificio">

#### Layout:
- **Barra laterale sinistra:** Fasi di provisioning, filtri, azioni, impostazioni
- **Area centrale:** Lista dispositivi
- **Barra laterale destra:** Pannelli Stage o dettagli dispositivo, tab Script, KVS, Webhook e OTA

### 2.3 Barra laterale sinistra

#### 2.3.1 Intestazione edificio

Mostra il nome dell'edificio attuale. Clicca per tornare alla pagina di benvenuto.
<div style="page-break-before: always;"></div>

#### 2.3.2 Fasi di provisioning

La pipeline di provisioning a 4 fasi:

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Fasi di provisioning">

**S1 - Provisioning AP:**
- Cerca dispositivi Shelly in modalità AP (Access Point)
- Configura le credenziali WiFi
- Disabilita cloud, BLE e modalità AP

**S2 - Adopt:**
- Scansiona la rete per nuovi dispositivi (range DHCP)
- Assegna IP statici dal pool
- Registra i dispositivi nel database

**S3 - OTA & Nomi:**
- Aggiorna il firmware all'ultima versione
- Sincronizza i nomi amichevoli sui dispositivi

**S4 - Configura:**
- Applica i profili dispositivo
- Configura ingressi, interruttori, tapparelle, ecc.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1: Provisioning AP

1. Clicca sul pulsante **S1**
2. L'adattatore WiFi della Stagebox cerca gli AP Shelly
3. I dispositivi trovati vengono configurati automaticamente, il contatore dispositivi aumenta
4. Clicca su **⏹ Stop** quando hai finito

<img src="screenshots/32-stage1-panel.png" width="450" alt="Pannello Stage 1">

> **Suggerimento:** Metti i dispositivi Shelly in modalità AP tenendo premuto il pulsante per 10+ secondi o eseguendo un reset di fabbrica.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2: Adopt

1. Clicca sul pulsante **S2**
2. Clicca su **Scansiona rete**
3. I nuovi dispositivi appaiono nella lista
4. Seleziona i dispositivi da adottare o clicca su **Adotta tutti**
5. I dispositivi ricevono IP statici e vengono registrati

<img src="screenshots/33-stage2-panel.png" width="300" alt="Pannello Stage 2">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3: OTA & Nomi

1. Clicca sul pulsante **S3**
2. I dispositivi allo Stage 2 sono elencati
3. Clicca su **Esegui Stage 3** per:
   - Aggiornare il firmware (se disponibile una versione più recente)
   - Sincronizzare i nomi amichevoli dal database ai dispositivi

<img src="screenshots/34-stage3-panel.png" width="300" alt="Pannello Stage 3">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4: Configura

1. Clicca sul pulsante **S4**
2. I dispositivi allo Stage 3 sono elencati
3. Clicca su **Esegui Stage 4** per applicare i profili:
   - Impostazioni interruttori (stato iniziale, spegnimento auto)
   - Impostazioni tapparelle (inverti direzione, limiti)
   - Configurazioni ingressi
   - Azioni personalizzate

<img src="screenshots/35-stage4-panel.png" width="300" alt="Pannello Stage 4">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filtri

Filtra la lista dispositivi per vari criteri:

| Filtro | Descrizione |
|--------|-------------|
| Stage | Mostra dispositivi a una fase di provisioning specifica |
| Stanza | Mostra dispositivi in una stanza specifica |
| Modello | Mostra tipi di dispositivo specifici |
| Stato | Dispositivi online/offline |

<img src="screenshots/36-filter-panel.png" width="200" alt="Pannello Filtri">

#### 2.3.8 Azioni

Operazioni di massa sui dispositivi selezionati:

| Azione | Descrizione |
|--------|-------------|
| 🔄 Aggiorna | Aggiorna lo stato dei dispositivi |
| 📋 Copia | Copia info dispositivo negli appunti |
| 📤 Esporta CSV | Esporta dispositivi selezionati |
| 🗑️ Rimuovi | Rimuovi dal database (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Lista dispositivi

L'area centrale mostra tutti i dispositivi nell'edificio attuale.

<img src="screenshots/40-device-list.png" width="500" alt="Lista dispositivi">

#### Colonne:

| Colonna | Descrizione |
|---------|-------------|
| ☑️ | Casella di selezione |
| Stato | Online (🟢) / Offline (🔴) |
| Nome | Nome amichevole del dispositivo |
| Stanza | Stanza assegnata |
| Posizione | Posizione nella stanza |
| Modello | Tipo di dispositivo |
| IP | Indirizzo IP attuale |
| Stage | Fase di provisioning attuale (S1-S4) |

#### Selezione:
- Clicca sulla casella per selezionare singoli dispositivi
- Clicca sulla casella dell'intestazione per selezionare tutti i visibili
- Maiusc+clic per selezione intervallo

#### Ordinamento:
- Clicca sull'intestazione della colonna per ordinare
- Clicca di nuovo per invertire l'ordine

<div style="page-break-before: always;"></div>

### 2.5 Barra laterale destra (Dettagli dispositivo)

Quando un dispositivo è selezionato, la barra laterale destra mostra informazioni dettagliate e azioni.

#### 2.5.1 Tab Info dispositivo

Informazioni base del dispositivo:

| Campo | Descrizione |
|-------|-------------|
| Nome | Nome amichevole modificabile |
| Stanza | Assegnazione stanza (modificabile) |
| Posizione | Posizione nella stanza (modificabile) |
| MAC | Indirizzo hardware |
| IP | Indirizzo di rete |
| Modello | Modello hardware |
| Firmware | Versione attuale |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Tab Info dispositivo">

<div style="page-break-before: always;"></div>

#### 2.5.2 Tab Script

Gestisci script sul dispositivo selezionato:

- Visualizza script installati
- Avvia/Ferma script
- Rimuovi script
- Distribuisci nuovi script

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Tab Script dispositivo">

#### 2.5.3 Tab KVS

Visualizza e modifica le voci Key-Value Store:

- Valori di sistema (sola lettura)
- Valori utente (modificabili)
- Aggiungi nuove voci
- Elimina voci

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Tab KVS dispositivo">
<div style="page-break-before: always;"></div>

#### 2.5.4 Tab Webhook

Configura i webhook del dispositivo:

- Visualizza webhook esistenti
- Aggiungi nuovi webhook
- Modifica URL e condizioni
- Elimina webhook

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Tab Webhook dispositivo">

#### 2.5.5 Tab Programmazioni

Gestisci le attività programmate:

- Visualizza programmazioni esistenti
- Aggiungi automazioni basate sul tempo
- Abilita/disabilita programmazioni
- Elimina programmazioni

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Tab Programmazioni dispositivo">

#### 2.5.6 Tab Componenti virtuali

Configura componenti virtuali sui dispositivi:

- Interruttori virtuali
- Sensori virtuali
- Componenti testo
- Componenti numerici

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Tab Virtuali dispositivo">

#### 2.5.7 Tab Aggiornamenti FW

Gestisci il firmware del dispositivo:

- Visualizza versione attuale
- Verifica aggiornamenti
- Applica aggiornamenti firmware

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Tab Aggiornamenti FW dispositivo">
<div style="page-break-before: always;"></div>

### 2.6 Gestione script

#### 2.6.1 Pool script (Admin)

Gestisci script condivisi disponibili per la distribuzione:

1. Vai alla pagina di benvenuto
2. Clicca su **📜 Pool script Shelly** (Admin)
3. Carica file JavaScript (.js)
4. Elimina script inutilizzati

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Dialogo Pool script">
<div style="page-break-before: always;"></div>

#### 2.6.2 Distribuire script

1. Seleziona i dispositivi di destinazione nella lista
2. Vai al tab **Script**
3. Seleziona la fonte: **Locale** (Pool script) o **Libreria GitHub**
4. Scegli uno script
5. Configura le opzioni:
   - ☑️ Esegui all'avvio
   - ☑️ Avvia dopo distribuzione
6. Clicca su **📤 Distribuisci**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Dialogo Distribuisci script">

<div style="page-break-before: always;"></div>

### 2.7 Impostazioni esperto (Avanzate)

> ⚠️ **Avviso:** Le impostazioni esperto consentono la configurazione diretta del comportamento di provisioning e dei parametri di sistema. Modifiche errate possono influire sul provisioning dei dispositivi. Usare con cautela!

Accesso tramite la sezione **Esperto** → **⚙️ Impostazioni edificio** nella barra laterale della pagina edificio.

Il dialogo Impostazioni edificio fornisce un'interfaccia a schede per configurare opzioni avanzate.

---

#### 2.7.1 Tab Provisioning

Controlla il comportamento del provisioning Stage 1 (modalità AP).

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Tab Esperto Provisioning">

| Impostazione | Descrizione | Predefinito |
|--------------|-------------|-------------|
| **Modalità loop** | Cerca continuamente nuovi dispositivi. Quando abilitato, Stage 1 continua a cercare nuovi AP Shelly dopo ogni provisioning riuscito. Disabilita per provisioning singolo dispositivo. | ☑️ Attivo |
| **Disabilita AP dopo provisioning** | Disattiva l'Access Point WiFi del dispositivo dopo la connessione alla tua rete. Consigliato per la sicurezza. | ☑️ Attivo |
| **Disabilita Bluetooth** | Disattiva il Bluetooth sui dispositivi provisionati. Risparmia energia e riduce la superficie di attacco. | ☑️ Attivo |
| **Disabilita Cloud** | Disabilita la connettività Shelly Cloud. I dispositivi saranno accessibili solo localmente. | ☑️ Attivo |
| **Disabilita MQTT** | Disattiva il protocollo MQTT sui dispositivi. Abilita se usi un sistema domotico con MQTT. | ☑️ Attivo |

---

#### 2.7.2 Tab OTA & Nomi

Configura il comportamento degli aggiornamenti firmware e la gestione dei nomi amichevoli durante Stage 3.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Tab Esperto OTA">

**Aggiornamenti firmware (OTA):**

| Impostazione | Descrizione | Predefinito |
|--------------|-------------|-------------|
| **Abilita aggiornamenti OTA** | Verifica e opzionalmente installa aggiornamenti firmware durante Stage 3. | ☑️ Attivo |
| **Modalità aggiornamento** | `Solo verifica`: Segnala aggiornamenti disponibili senza installare. `Verifica & Aggiorna`: Installa automaticamente gli aggiornamenti disponibili. | Solo verifica |
| **Timeout (secondi)** | Tempo massimo di attesa per le operazioni OTA. Aumenta per reti lente. | 20 |

**Nomi amichevoli:**

| Impostazione | Descrizione | Predefinito |
|--------------|-------------|-------------|
| **Abilita nomi amichevoli** | Applica nomi stanza/posizione ai dispositivi durante Stage 3. I nomi vengono memorizzati nella configurazione del dispositivo. | ☑️ Attivo |
| **Completa nomi mancanti** | Genera automaticamente nomi per dispositivi senza assegnazione. Usa il pattern `<Modello>_<Suffisso-MAC>`. | ☐ Disattivo |

<div style="page-break-before: always;"></div>

#### 2.7.3 Tab Esporta

Configura le impostazioni di esportazione CSV per etichette dispositivi e report.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Tab Esperto Esporta">

**Delimitatore CSV:**

Scegli il separatore di colonne per i file CSV esportati:
- **Punto e virgola (;)** - Predefinito, funziona con le versioni Excel europee
- **Virgola (,)** - Formato CSV standard
- **Tab** - Per valori separati da tabulazione

**Colonne predefinite:**

Seleziona quali colonne appaiono nei file CSV esportati. Colonne disponibili:

| Colonna | Descrizione |
|---------|-------------|
| `id` | Indirizzo MAC del dispositivo (identificatore univoco) |
| `ip` | Indirizzo IP attuale |
| `hostname` | Hostname del dispositivo |
| `fw` | Versione firmware |
| `model` | Nome modello amichevole |
| `hw_model` | ID modello hardware |
| `friendly_name` | Nome dispositivo assegnato |
| `room` | Assegnazione stanza |
| `location` | Posizione nella stanza |
| `assigned_at` | Quando il dispositivo è stato provisionato |
| `last_seen` | Timestamp ultima comunicazione |
| `stage3_friendly_status` | Stato assegnazione nome |
| `stage3_ota_status` | Stato aggiornamento firmware |
| `stage4_status_result` | Risultato fase di configurazione |

<div style="page-break-before: always;"></div>

#### 2.7.4 Tab Model Map

Definisci nomi di visualizzazione personalizzati per gli ID modello hardware Shelly.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Tab Esperto Model Map">

La Model Map traduce gli identificatori hardware interni (es: `SNSW-001X16EU`) in nomi leggibili (es: `Shelly Plus 1`).

**Utilizzo:**
1. Inserisci l'**ID hardware** esattamente come riportato dal dispositivo
2. Inserisci il tuo **Nome visualizzato** preferito
3. Clicca su **+ Aggiungi modello** per aggiungere altre voci
4. Clicca su **🗑️** per rimuovere una voce

> **Suggerimento:** Controlla l'interfaccia web del dispositivo o la risposta API per trovare la stringa esatta dell'ID hardware.

<div style="page-break-before: always;"></div>

#### 2.7.5 Tab Avanzate (Editor YAML)

Modifica diretta dei file di configurazione per scenari avanzati.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Tab Esperto Avanzate">

**File disponibili:**

| File | Descrizione |
|------|-------------|
| `config.yaml` | Configurazione principale edificio (range IP, database dispositivi, impostazioni provisioning) |
| `profiles/*.yaml` | Profili configurazione dispositivi per Stage 4 |

**Funzionalità:**
- Validazione sintassi (indicatore verde/rosso)
- Seleziona file dal menu a tendina
- Modifica contenuto direttamente
- Tutte le modifiche vengono salvate automaticamente prima del salvataggio

**Indicatore di validazione:**
- 🟢 Verde: Sintassi YAML valida
- 🔴 Rosso: Errore di sintassi (passa sopra per i dettagli)

> **Raccomandazione:** Usa gli altri tab per la configurazione normale. Usa l'editor YAML solo quando devi modificare impostazioni non esposte nell'interfaccia, o per la risoluzione dei problemi.

<div style="page-break-before: always;"></div>

### 2.8 Manutenzione sistema

#### 2.8.1 Aggiornamenti Stagebox

Verifica e installa aggiornamenti software Stagebox:

1. Vai alla pagina di benvenuto
2. Clicca su **📦 Aggiornamento Stagebox** (Admin)
3. Vengono mostrate le versioni attuale e disponibile
4. Clicca su **⬇️ Installa aggiornamento** se disponibile
5. Attendi l'installazione e il riavvio automatico

<img src="screenshots/80-stagebox-update.png" width="450" alt="Dialogo Aggiornamento Stagebox">
<div style="page-break-before: always;"></div>

#### 2.8.2 Aggiornamenti sistema

Verifica e installa aggiornamenti del sistema operativo:

1. Vai alla pagina di benvenuto
2. Clicca su **🖥️ Aggiornamenti sistema** (Admin)
3. Vengono elencati gli aggiornamenti di sicurezza e sistema
4. Clicca su **⬇️ Installa aggiornamenti**
5. Il sistema potrebbe riavviarsi se necessario

<img src="screenshots/81-system-updates.png" width="450" alt="Dialogo Aggiornamenti sistema">

---

<div style="page-break-before: always;"></div>

### 2.9 Report & Documentazione

Stagebox fornisce funzionalità di reportistica complete per la documentazione professionale delle installazioni. I report includono inventari dispositivi, dettagli di configurazione, e possono essere personalizzati con il branding dell'installatore.

#### 2.9.1 Profilo installatore

Il profilo installatore contiene le informazioni della tua azienda che appaiono su tutti i report generati. È un'impostazione globale condivisa tra tutti gli edifici.

**Accesso al profilo installatore:**

1. Vai alla pagina di benvenuto
2. Clicca su **🏢 Profilo installatore** (Admin richiesto)

**Campi disponibili:**

| Campo | Descrizione |
|-------|-------------|
| Nome azienda | Nome della tua azienda o attività |
| Indirizzo | Indirizzo postale (multilinea supportato) |
| Telefono | Numero di telefono di contatto |
| E-mail | Indirizzo e-mail di contatto |
| Sito web | URL del sito web aziendale |
| Logo | Immagine logo aziendale (PNG, JPG, max 2MB) |

**Linee guida per il logo:**
- Dimensione consigliata: 400×200 pixel o proporzioni simili
- Formati: PNG (sfondo trasparente consigliato) o JPG
- Dimensione massima file: 2MB
- Il logo appare nell'intestazione dei report PDF

> **Suggerimento:** Completa il profilo installatore prima di generare il tuo primo report per assicurare una documentazione dall'aspetto professionale.

<img src="screenshots/90-installer-profile.png" width="450" alt="Dialogo Profilo installatore">

<div style="page-break-before: always;"></div>

#### 2.9.2 Profilo edificio (Informazioni oggetto)

Ogni edificio può avere il proprio profilo con informazioni specifiche del cliente e del progetto. Questi dati appaiono nei report generati per quell'edificio.

**Accesso al profilo edificio:**

1. Apri la pagina edificio
2. Vai alla sezione **Esperto** nella barra laterale
3. Clicca su **⚙️ Impostazioni edificio**
4. Seleziona il tab **Oggetto**

**Campi disponibili:**

| Campo | Descrizione |
|-------|-------------|
| Nome oggetto | Nome del progetto o proprietà (es: "Villa Müller") |
| Nome cliente | Nome del cliente |
| Indirizzo | Indirizzo della proprietà (multilinea supportato) |
| Telefono contatto | Numero di telefono del cliente |
| E-mail contatto | Indirizzo e-mail del cliente |
| Note | Note aggiuntive (appaiono nei report) |

> **Nota:** Il nome oggetto viene usato come titolo del report. Se non impostato, viene usato il nome dell'edificio.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Tab Profilo edificio">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshot

Uno snapshot cattura lo stato completo di tutti i dispositivi in un edificio in un momento specifico. Gli snapshot sono memorizzati come bundle ZIP contenenti dati dispositivi e file di configurazione.

**Creare uno snapshot:**

1. Apri la pagina edificio
2. Vai alla sezione **Audit** nella barra laterale
3. Clicca su **📸 Snapshot**
4. Attendi il completamento della scansione

**Gestione snapshot:**

| Azione | Descrizione |
|--------|-------------|
| 📥 Scarica | Scarica il bundle ZIP dello snapshot |
| 🗑️ Elimina | Rimuovi lo snapshot |

**Contenuto ZIP dello snapshot:**

Ogni snapshot viene memorizzato come file ZIP contenente:

| File | Descrizione |
|------|-------------|
| `snapshot.json` | Dati completi scansione dispositivi (IP, MAC, config, stato) |
| `installer_profile.json` | Informazioni aziendali installatore |
| `installer_logo.png` | Logo aziendale (se configurato) |
| `ip_state.json` | Database dispositivi con assegnazioni stanza/posizione |
| `building_profile.json` | Informazioni oggetto/cliente |
| `config.yaml` | Configurazione edificio |
| `shelly_model_map.yaml` | Mappature nomi modello personalizzate (se configurate) |
| `scripts/*.js` | Script distribuiti (se presenti) |

> **Suggerimento:** Gli snapshot sono bundle autonomi che possono essere usati con strumenti di documentazione esterni o archiviati per riferimento futuro.

**Pulizia automatica:**

Stagebox mantiene automaticamente solo i 5 snapshot più recenti per edificio per risparmiare spazio di archiviazione.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Dialogo Snapshot">

<div style="page-break-before: always;"></div>

#### 2.9.4 Generatore report

Genera report di installazione professionali in formato PDF o Excel.

**Generare un report:**

1. Apri la pagina edificio
2. Vai alla sezione **Audit** nella barra laterale
3. Clicca su **📊 Generatore report**
4. Configura le opzioni del report:
   - **Snapshot**: Crea nuovo o seleziona esistente
   - **Lingua**: Lingua del report (DE, EN, FR, IT, NL)
   - **Formato**: PDF o Excel (XLSX)
5. Clicca su **Genera**

<img src="screenshots/93-report-generator.png" width="450" alt="Dialogo Generatore report">

**Contenuto report PDF:**

Il report PDF include:
- **Intestazione**: Logo aziendale, titolo report, data di generazione
- **Informazioni oggetto**: Nome cliente, indirizzo, contatti
- **Riepilogo**: Totale dispositivi, stanze e tipi di dispositivo
- **Tabella dispositivi**: Inventario completo con codici QR

**Colonne tabella dispositivi:**

| Colonna | Descrizione |
|---------|-------------|
| QR | Codice QR collegato all'interfaccia web del dispositivo |
| Stanza | Stanza assegnata |
| Posizione | Posizione nella stanza |
| Nome | Nome amichevole del dispositivo |
| Modello | Tipo di dispositivo |
| IP | Indirizzo di rete |
| FW | Versione firmware |
| MAC | Ultimi 6 caratteri dell'indirizzo MAC |
| SWTAK | Flag funzionalità (vedi sotto) |

**Flag funzionalità (SWTAK):**

Ogni dispositivo mostra quali funzionalità sono configurate:

| Flag | Significato | Fonte |
|------|-------------|-------|
| **S** | Script | Il dispositivo ha script installati |
| **W** | Webhook | Il dispositivo ha webhook configurati |
| **T** | Timer | Timer auto-on o auto-off attivi |
| **A** | Programmazioni | Automazioni programmate configurate |
| **K** | KVS | Voci Key-Value Store presenti |

I flag attivi sono evidenziati, i flag inattivi sono in grigio.

**Report Excel:**

L'esportazione Excel contiene le stesse informazioni del PDF in formato foglio di calcolo:
- Foglio singolo con tutti i dispositivi
- Intestazione con metadati del report
- Legenda che spiega i flag SWTAK
- Colonne ottimizzate per filtro e ordinamento

> **Suggerimento:** Usa il formato Excel quando devi elaborare ulteriormente i dati o creare documentazione personalizzata.

<div style="page-break-before: always;"></div>

#### 2.9.5 Audit configurazione

La funzione Audit confronta lo stato live attuale di tutti i dispositivi con uno snapshot di riferimento per rilevare modifiche alla configurazione, nuovi dispositivi o dispositivi offline.

**Eseguire un audit:**

1. Apri la pagina edificio
2. Vai alla sezione **Audit** nella barra laterale
3. Clicca su **🔍 Esegui audit**
4. Seleziona uno snapshot di riferimento dal menu a tendina
5. Clicca su **🔍 Avvia audit**

<img src="screenshots/94-audit-setup.png" width="450" alt="Dialogo Setup audit">

Il sistema eseguirà una nuova scansione di tutti i dispositivi e li confronterà con lo snapshot selezionato.

**Risultati audit:**

| Stato | Icona | Descrizione |
|-------|-------|-------------|
| OK | ✅ | Dispositivo invariato dallo snapshot |
| Modificato | ⚠️ | Rilevate differenze di configurazione |
| Offline | ❌ | Il dispositivo era nello snapshot ma non risponde |
| Nuovo | 🆕 | Dispositivo trovato che non era nello snapshot |

<img src="screenshots/95-audit-results.png" width="500" alt="Risultati audit">

**Modifiche rilevate:**

L'audit rileva e segnala:
- Modifiche indirizzo IP
- Modifiche nome dispositivo
- Aggiornamenti firmware
- Modifiche configurazione (tipi ingresso, impostazioni interruttore, impostazioni tapparelle)
- Modifiche impostazioni WiFi
- Dispositivi nuovi o mancanti

**Casi d'uso:**

- **Verifica post-installazione**: Conferma che tutti i dispositivi sono configurati come documentato
- **Controlli di manutenzione**: Rileva modifiche inaspettate dall'ultima visita
- **Risoluzione problemi**: Identifica quali impostazioni sono state modificate
- **Documentazione di consegna**: Verifica che l'installazione corrisponda alle specifiche prima della consegna

> **Suggerimento:** Crea uno snapshot dopo aver completato un'installazione da usare come riferimento per audit futuri.

<div style="page-break-before: always;"></div>

## Appendice

### A. Scorciatoie da tastiera

| Scorciatoia | Azione |
|-------------|--------|
| `Escape` | Chiudi dialogo/modale |
| `Enter` | Conferma dialogo |

### B. Indicatori di stato

| Icona | Significato |
|-------|-------------|
| 🟢 (verde) | Dispositivo online |
| 🔴 (rosso) | Dispositivo offline |
| S1-S4 | Fase di provisioning attuale |
| ⚡ | Aggiornamento firmware disponibile |

### C. Risoluzione problemi

**Impossibile accedere all'interfaccia Web:**
- Verifica la connessione Ethernet
- Controlla se la Stagebox ha un IP (lista DHCP del router o display OLED)
- Prova l'indirizzo IP direttamente invece di .local

**PIN Admin dimenticato:**
- Tieni premuto il pulsante OLED per **10+ secondi**
- Il display mostrerà "PIN RESET" e "PIN = 0000"
- Il PIN è ora reimpostato a `0000` predefinito
- Accedi con `0000` e cambia il PIN immediatamente

**Dispositivi non trovati allo Stage 1:**
- Assicurati che il dispositivo sia in modalità AP (LED lampeggiante)
- Avvicina la Stagebox al dispositivo
- Controlla la connessione dell'adattatore WiFi

**Dispositivi non trovati allo Stage 2:**
- Verifica le impostazioni del range DHCP
- Controlla se il dispositivo è connesso al WiFi corretto
- Attendi 30 secondi dopo lo Stage 1

**Lo Stage 4 fallisce:**
- Controlla la compatibilità del dispositivo
- Verifica che esista un profilo per il tipo di dispositivo
- Controlla che il dispositivo sia online

**Errori backup USB:**
- Rimuovi e reinserisci la chiavetta USB
- Se l'errore persiste, aggiorna la pagina (Ctrl+F5)
- Assicurati che la chiavetta USB sia formattata per Stagebox (Admin → Formatta chiavetta USB)

**Generazione report lenta:**
- Installazioni grandi (50+ dispositivi) possono richiedere 10-20 secondi
- La generazione PDF include la creazione di codici QR per ogni dispositivo
- Usa il formato Excel per una generazione più veloce senza codici QR

---

*Manuale utente Stagebox Web-UI - Versione 1.5*