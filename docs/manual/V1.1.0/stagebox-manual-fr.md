# Manuel d'utilisation Stagebox Web-UI

> *Ce manuel correspond à la Stagebox Pro Version 1.1.0*

## Partie 1 : Premiers pas

Ce guide vous accompagne dans la configuration initiale de votre Stagebox et la création de votre premier projet de bâtiment.
  


<img src="screenshots/01-stagebox-picture.png" width="700" alt="Product Picture">

### 1.1 Connexion de la Stagebox

1. Connectez la Stagebox à votre réseau à l'aide d'un câble Ethernet
2. Branchez l'alimentation
3. Attendez environ 60 secondes le démarrage du système
4. L'écran OLED en façade affiche les informations de connexion

> **Remarque :** La Stagebox nécessite une connexion réseau filaire. Le WiFi est utilisé uniquement pour le provisionnement des appareils Shelly.

<div style="page-break-before: always;"></div>

### 1.2 Utilisation de l'écran OLED

La Stagebox dispose d'un écran OLED intégré qui alterne automatiquement entre plusieurs écrans d'information (toutes les 10 secondes).

**Écran 1 — Splash (Identification principale) :**

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

Cet écran affiche :
- Le titre « STAGEBOX »
- L'adresse IP pour l'accès web
- Le suffixe MAC (6 derniers caractères pour l'identification)

**Écran 2 — Infos bâtiment :**
- Version actuelle de la Stagebox
- Nom du bâtiment actif

**Écran 3 — État du système :**
- Température et charge CPU
- Température NVMe
- Utilisation RAM et disque

**Écran 4 — Réseau :**
- Adresse IP Ethernet
- Adresse IP WLAN (si connecté)
- Nom d'hôte

**Écran 5 — Horloge :**
- Heure actuelle avec secondes
- Date actuelle

<div style="page-break-before: always;"></div>

**Fonctions du bouton OLED :**

Le bouton du boîtier Argon ONE contrôle l'écran :

| Durée de pression | Action |
|--------------------|--------|
| Pression courte (<2s) | Passer à l'écran suivant |
| Pression longue (2–10s) | Activer/désactiver l'écran |
| Pression très longue (10s+) | Réinitialiser le PIN Admin à `0000` |

> **Astuce :** Utilisez l'écran Splash ou Réseau pour trouver l'adresse IP nécessaire pour accéder à la Web-UI.

<div style="page-break-before: always;"></div>

### 1.3 Accès à l'interface web

Trouvez l'adresse IP sur l'écran OLED (écran Splash ou Réseau), puis ouvrez un navigateur web :

```
http://<ADRESSE-IP>:5000
```

Par exemple : `http://192.168.1.100:5000`

**Alternative via le nom d'hôte :**

```
http://stagebox-XXXXXX.local:5000
```

Remplacez `XXXXXX` par le suffixe MAC affiché sur l'écran OLED.

> **Remarque :** Le nom d'hôte `.local` nécessite le support mDNS (Bonjour). S'il ne fonctionne pas, utilisez directement l'adresse IP.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Greeting Page - First Access">
<div style="page-break-before: always;"></div>
### 1.4 Connexion en tant qu'Admin

Les fonctions administratives sont protégées par un PIN. Le PIN par défaut est **0000**.

1. Cliquez sur **🔒 Admin** dans la section Admin
2. Entrez le PIN (par défaut : `0000`)
3. Cliquez sur **Confirmer**

Vous êtes maintenant connecté en tant qu'Admin (affiché comme 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Admin Login">

> **Recommandation de sécurité :** Changez le PIN par défaut immédiatement après la première connexion (voir section 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Création de votre premier bâtiment

Un « bâtiment » dans la Stagebox représente un projet ou un site d'installation. Chaque bâtiment possède sa propre base de données d'appareils, son pool IP et sa configuration.

1. Assurez-vous d'être connecté en tant qu'Admin (🔓 Admin visible)
2. Cliquez sur **➕ Nouveau bâtiment**
3. Entrez un nom de bâtiment (par ex. `maison_client`)
   - Utilisez uniquement des minuscules, des chiffres et des tirets bas
   - Les espaces et caractères spéciaux sont automatiquement convertis
4. Cliquez sur **Créer**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="New Building Dialog">

Le bâtiment est créé et **s'ouvre automatiquement** avec le dialogue de configuration WiFi.

---

> ⚠️ **CRITIQUE : Configurez correctement les paramètres WiFi !**
>
> Les paramètres WiFi que vous entrez ici déterminent le réseau auquel vos appareils Shelly se connecteront. **Des paramètres incorrects rendront les appareils inaccessibles !**
>
> - Vérifiez l'orthographe du SSID (sensible à la casse !)
> - Vérifiez que le mot de passe est correct
> - Assurez-vous que les plages IP correspondent à votre réseau réel
>
> Les appareils provisionnés avec de mauvais identifiants WiFi doivent être réinitialisés et reprovisionnés.

<div style="page-break-before: always;"></div>

### 1.6 Configuration WiFi et plages IP

Après la création d'un bâtiment, le dialogue **Paramètres du bâtiment** apparaît automatiquement.

<img src="screenshots/07-building-settings.png" width="200" alt="Building Settings">

#### Configuration WiFi

Entrez les identifiants WiFi auxquels les appareils Shelly doivent se connecter :

**WiFi principal (requis) :**
- SSID : Votre nom de réseau (par ex. `HomeNetwork`)
- Mot de passe : Votre mot de passe WiFi

**WiFi de secours (optionnel) :**
- Un réseau de secours si le principal n'est pas disponible

<img src="screenshots/08-wifi-settings.png" width="450" alt="WiFi Settings">

#### Plages d'adresses IP

Configurez le pool d'IP statiques pour les appareils Shelly :

**Pool Shelly :**
- De : Première IP pour les appareils (par ex. `192.168.1.50`)
- À : Dernière IP pour les appareils (par ex. `192.168.1.99`)

**Passerelle :**
- Généralement l'IP de votre routeur (par ex. `192.168.1.1`)
- Laisser vide pour la détection automatique (.1)

**Plage de scan DHCP (optionnel) :**
- Plage où les nouveaux appareils apparaissent après une réinitialisation usine
- Laisser vide pour scanner tout le sous-réseau (plus lent)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="IP Range Settings">

> **Avertissement :** Les plages IP doivent correspondre à votre réseau réel ! Les appareils seront inaccessibles s'ils sont configurés avec un mauvais sous-réseau.

5. Cliquez sur **💾 Enregistrer**

<div style="page-break-before: always;"></div>

### 1.7 Modification du PIN Admin

Pour modifier votre PIN Admin (par défaut `0000`) :

1. Cliquez sur **🔓 Admin** (doit être connecté)
2. Cliquez sur **🔑 Modifier le PIN**
3. Entrez le nouveau PIN (minimum 4 chiffres)
4. Confirmez le nouveau PIN
5. Cliquez sur **Enregistrer**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="Change PIN Dialog">

> **Important :** Mémorisez ce PIN ! Il protège toutes les fonctions administratives, y compris la suppression de bâtiments et les paramètres système.

### 1.8 Étapes suivantes

Votre Stagebox est maintenant prête pour le provisionnement d'appareils. Passez à la partie 2 pour en savoir plus sur :
- Le provisionnement de nouveaux appareils Shelly (Stage 1–4)
- La gestion des appareils
- La création de sauvegardes

---

<div style="page-break-before: always;"></div>

## Partie 2 : Référence des fonctions

### 2.1 Page d'accueil (Sélection du bâtiment)

La page d'accueil est le point de départ après l'accès à la Stagebox. Elle affiche tous les bâtiments et fournit les fonctions système.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Greeting Page Overview">

#### 2.1.1 Liste des bâtiments

La zone centrale affiche tous les bâtiments disponibles sous forme de cartes.

Chaque carte de bâtiment affiche :
- Nom du bâtiment
- Résumé de la plage IP
- Nombre d'appareils

**Actions (mode Admin uniquement) :**
- ✏️ Renommer le bâtiment
- 🗑️ Supprimer le bâtiment

<img src="screenshots/21-building-cards.png" width="200" alt="Building Cards">

**Sélection d'un bâtiment :**
- Clic simple pour sélectionner
- Double-clic pour ouvrir directement
- Cliquez sur **Ouvrir →** après la sélection

#### 2.1.2 Section Système

Située à gauche de la liste des bâtiments :

| Bouton | Fonction | Admin requis |
|--------|----------|-------------|
| 💾 Sauvegarde USB | Créer une sauvegarde de tous les bâtiments sur clé USB | Non |
| 🔄 Redémarrer | Redémarrer la Stagebox | Non |
| ⏻ Arrêter | Arrêter la Stagebox en toute sécurité | Non |

> **Important :** Utilisez toujours **Arrêter** avant de débrancher l'alimentation pour éviter la corruption des données.

#### 2.1.3 Section Admin

Fonctions administratives (nécessite le PIN Admin) :

| Bouton | Fonction |
|--------|----------|
| 🔒/🔓 Admin | Connexion/Déconnexion |
| ➕ Nouveau bâtiment | Créer un nouveau bâtiment |
| 📤 Exporter tous les bâtiments | Télécharger un ZIP de tous les bâtiments |
| 📥 Importer bâtiment(s) | Importer depuis un fichier ZIP |
| 📜 Shelly Script Pool | Gérer les scripts partagés |
| 📂 Restaurer depuis USB | Restaurer les bâtiments depuis une sauvegarde USB |
| 🔌 Formater clé USB | Préparer la clé USB pour les sauvegardes |
| 🔑 Modifier le PIN | Modifier le PIN Admin |
| 📦 Mise à jour Stagebox | Vérifier les mises à jour logicielles |
| 🖥️ Mises à jour système | Vérifier les mises à jour OS |
| 🌐 Langue | Changer la langue de l'interface |
| 🏢 Profil installateur | Configurer les informations de l'entreprise pour les rapports |


#### 2.1.4 Sauvegarde USB

**Création d'une sauvegarde :**

1. Insérez une clé USB (tout format)
2. Si non formatée pour Stagebox : Cliquez sur **🔌 Formater clé USB** (Admin)
3. Cliquez sur **💾 Sauvegarde USB**
4. Attendez le message de fin
5. La clé USB peut maintenant être retirée en toute sécurité

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="USB Format Dialog">

**Restauration depuis USB :**

1. Insérez la clé USB contenant les sauvegardes
2. Cliquez sur **📂 Restaurer depuis USB** (Admin)
3. Sélectionnez une sauvegarde dans la liste
4. Choisissez les bâtiments à restaurer
5. Cliquez sur **Restaurer la sélection**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="USB Restore Dialog">

#### 2.1.5 Export/Import de bâtiments

**Export :**
1. Cliquez sur **📤 Exporter tous les bâtiments** (Admin)
2. Un fichier ZIP contenant toutes les données des bâtiments est téléchargé

**Import :**
1. Cliquez sur **📥 Importer bâtiment(s)** (Admin)
2. Glissez-déposez un fichier ZIP ou cliquez pour sélectionner
3. Choisissez les bâtiments à importer
4. Sélectionnez l'action pour les bâtiments existants (ignorer/écraser)
5. Cliquez sur **Importer la sélection**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Import Buildings Dialog">

<div style="page-break-before: always;"></div>

### 2.2 Page du bâtiment

La page du bâtiment est l'espace de travail principal pour le provisionnement et la gestion des appareils dans un bâtiment spécifique.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Building Page Overview">

#### Disposition :
- **Barre latérale gauche :** Étapes de provisionnement, filtres, actions, paramètres
- **Zone centrale :** Liste des appareils
- **Barre latérale droite :** Panneaux Stage ou détails de l'appareil, onglets Script, KVS, Webhook, Planification et OTA

### 2.3 Barre latérale gauche

#### 2.3.1 En-tête du bâtiment

Affiche le nom du bâtiment actuel. Cliquez pour revenir à la page d'accueil.
<div style="page-break-before: always;"></div>

#### 2.3.2 Étapes de provisionnement

Le pipeline de provisionnement en 4 étapes :

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Provisioning Stages">

**S1 — Provisionnement AP :**
- Recherche les appareils Shelly en mode AP (Access Point)
- Configure les identifiants WiFi
- Désactive le cloud, le BLE et le mode AP

**S2 — Adoption :**
- Scanne le réseau pour les nouveaux appareils (plage DHCP)
- Attribue des IP statiques depuis le pool
- Enregistre les appareils dans la base de données

**S3 — OTA & Noms :**
- Met à jour le firmware vers la dernière version
- Synchronise les noms conviviaux vers les appareils

**S4 — Configuration :**
- Applique les profils d'appareils
- Configure les entrées, interrupteurs, volets, etc.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1 : Provisionnement AP

1. Cliquez sur le bouton **S1**
2. L'adaptateur WiFi de la Stagebox recherche les AP Shelly
3. Les appareils trouvés sont automatiquement configurés, le compteur d'appareils s'incrémente
4. Cliquez sur **⏹ Stop** lorsque terminé

<img src="screenshots/32-stage1-panel.png" width="450" alt="Stage 1 Panel">

> **Astuce :** Mettez les appareils Shelly en mode AP en maintenant le bouton enfoncé pendant 10+ secondes ou en effectuant une réinitialisation usine.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2 : Adoption

1. Cliquez sur le bouton **S2**
2. Cliquez sur **Scanner le réseau**
3. Les nouveaux appareils apparaissent dans la liste
4. Sélectionnez les appareils à adopter ou cliquez sur **Adopter tout**
5. Les appareils reçoivent des IP statiques et sont enregistrés

<img src="screenshots/33-stage2-panel.png" width="300" alt="Stage 2 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3 : OTA & Noms

1. Cliquez sur le bouton **S3**
2. Les appareils au Stage 2 sont listés
3. Cliquez sur **Exécuter Stage 3** pour :
   - Mettre à jour le firmware (si une version plus récente est disponible)
   - Synchroniser les noms conviviaux depuis la base de données vers les appareils

<img src="screenshots/34-stage3-panel.png" width="300" alt="Stage 3 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4 : Configuration

1. Cliquez sur le bouton **S4**
2. Les appareils au Stage 3 sont listés
3. Cliquez sur **Exécuter Stage 4** pour appliquer les profils :
   - Paramètres d'interrupteur (état initial, arrêt automatique)
   - Paramètres de volet (inversion de direction, limites)
   - Configurations d'entrée
   - Actions personnalisées

<img src="screenshots/35-stage4-panel.png" width="300" alt="Stage 4 Panel">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filtres

Filtrez la liste des appareils selon divers critères :

| Filtre | Description |
|--------|-------------|
| Stage | Afficher les appareils à une étape de provisionnement spécifique |
| Pièce | Afficher les appareils dans une pièce spécifique |
| Modèle | Afficher des types d'appareils spécifiques |
| Statut | Appareils en ligne/hors ligne |

<img src="screenshots/36-filter-panel.png" width="200" alt="Filter Panel">

#### 2.3.8 Actions

Opérations en masse sur les appareils sélectionnés :

| Action | Description |
|--------|-------------|
| 🔄 Actualiser | Mettre à jour le statut des appareils |
| 📋 Copier | Copier les infos de l'appareil dans le presse-papiers |
| 📤 Exporter CSV | Exporter les appareils sélectionnés |
| 🗑️ Supprimer | Supprimer de la base de données (Admin) |

<div style="page-break-before: always;"></div>

### 2.4 Liste des appareils

La zone centrale affiche tous les appareils du bâtiment actuel.

<img src="screenshots/40-device-list.png" width="500" alt="Device List">

#### Colonnes :

| Colonne | Description |
|---------|-------------|
| ☑️ | Case à cocher de sélection |
| Statut | En ligne (🟢) / Hors ligne (🔴) |
| Nom | Nom convivial de l'appareil |
| Pièce | Pièce attribuée |
| Emplacement | Position dans la pièce |
| Modèle | Type d'appareil |
| IP | Adresse IP actuelle |
| Stage | Étape de provisionnement actuelle (S1–S4) |

#### Sélection :
- Cliquez sur la case pour sélectionner des appareils individuels
- Cliquez sur la case d'en-tête pour sélectionner tous les appareils visibles
- Shift+clic pour une sélection par plage

#### Tri :
- Cliquez sur l'en-tête de colonne pour trier
- Cliquez à nouveau pour inverser l'ordre

<div style="page-break-before: always;"></div>

### 2.5 Barre latérale droite (Détails de l'appareil)

Lorsqu'un appareil est sélectionné, la barre latérale droite affiche des informations détaillées et des actions.

#### 2.5.1 Onglet Info appareil

Informations de base sur l'appareil :

| Champ | Description |
|-------|-------------|
| Nom | Nom convivial modifiable |
| Pièce | Attribution de pièce (modifiable) |
| Emplacement | Position dans la pièce (modifiable) |
| MAC | Adresse matérielle |
| IP | Adresse réseau |
| Modèle | Modèle matériel |
| Firmware | Version actuelle |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Device Info Tab">

<div style="page-break-before: always;"></div>

#### 2.5.2 Onglet Scripts

Gérer les scripts sur l'appareil sélectionné :

- Voir les scripts installés
- Démarrer/arrêter les scripts
- Supprimer les scripts
- Déployer de nouveaux scripts

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Device Scripts Tab">

#### 2.5.3 Onglet KVS

Afficher et modifier les entrées du Key-Value Store :

- Valeurs système (lecture seule)
- Valeurs utilisateur (modifiables)
- Ajouter de nouvelles entrées
- Supprimer des entrées

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Device KVS Tab">
<div style="page-break-before: always;"></div>

#### 2.5.4 Onglet Webhooks

Configurer les webhooks de l'appareil :

- Voir les webhooks existants
- Ajouter de nouveaux webhooks
- Modifier les URLs et conditions
- Supprimer les webhooks

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Device Webhooks Tab">
<div style="page-break-before: always;"></div>

#### 2.5.5 Onglet Planifications

L'onglet Planifications permet de créer, gérer et déployer des automatisations temporelles sur les appareils Shelly. Les planifications sont enregistrées comme modèles et peuvent être déployées simultanément sur plusieurs appareils compatibles.

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Device Schedules Tab">

**Vue d'ensemble de l'onglet :**

L'onglet Planifications est divisé en trois zones :

1. **Liste des modèles** — modèles de planification enregistrés avec contrôles de modification/suppression
2. **Appareils cibles** — liste de cases à cocher pour sélectionner les cibles de déploiement
3. **Boutons d'action** — Déployer, Statut et Tout supprimer

##### Créer une planification

1. Cliquez sur **+ Nouveau** pour ouvrir l'éditeur de planification
2. Entrez un **Nom** et une **Description** optionnelle

<img src="screenshots/54a-schedule-editor-modal.png" width="500" alt="Schedule Editor Modal">

**Colonne gauche — Temporisation :**

Sélectionnez l'un des quatre modes de temporisation :

| Mode | Description |
|------|-------------|
| 🕐 **Heure** | Définir une heure spécifique de la journée (heures et minutes) |
| 🌅 **Lever du soleil** | Déclenchement au lever du soleil, avec décalage optionnel |
| 🌇 **Coucher du soleil** | Déclenchement au coucher du soleil, avec décalage optionnel |
| 📅 **Intervalle** | Répétition à intervalles réguliers — choisissez parmi les préréglages (toutes les 5 min, 15 min, 30 min, toutes les heures, toutes les 2 heures) ou entrez des valeurs personnalisées en minutes/heures |

Sous le mode de temporisation, sélectionnez les **jours de la semaine** à l'aide des cases à cocher (lun–dim).

Le champ **timespec** affiche l'expression cron Shelly générée (lecture seule). En dessous, un aperçu affiche les prochaines heures d'exécution planifiées.

La case **Activé** contrôle si la planification est active après le déploiement.

**Colonne droite — Actions :**

3. Sélectionnez un **Appareil de référence** dans le menu déroulant — Stagebox interroge cet appareil pour déterminer les composants et actions disponibles (par ex. Switch, Cover, Light)
4. Ajoutez une ou plusieurs **Actions** (jusqu'à 5 par planification) en cliquant sur **+ Ajouter une action** :
   - Les méthodes disponibles dépendent des composants de l'appareil de référence
   - Exemples : `Switch.Set` (on/off), `Cover.GoToPosition` (0–100), `Light.Set` (on/off/luminosité)
   - Supprimez une action avec le bouton **✕**

5. Cliquez sur **💾 Enregistrer** pour sauvegarder le modèle, ou **Annuler** pour abandonner

> **Astuce :** L'appareil de référence détermine quelles actions sont disponibles. Choisissez un appareil qui possède les composants que vous souhaitez contrôler.

##### Modifier une planification

- Cliquez sur le bouton **✏️ Modifier** à côté d'un modèle, ou **double-cliquez** sur le nom du modèle
- L'éditeur de planification s'ouvre pré-rempli avec les paramètres existants
- Modifiez et cliquez sur **💾 Enregistrer**

##### Déployer des planifications

1. Sélectionnez un modèle de planification dans la liste
2. Cochez les appareils cibles dans la section **Appareils cibles**
   - Utilisez **Tout sélectionner** / **Aucun** pour une sélection rapide
   - Les appareils incompatibles (composants requis manquants) sont automatiquement ignorés lors du déploiement
3. Cliquez sur **📤 Déployer**
4. Les résultats sont affichés par appareil avec le statut succès/échec

> **Remarque :** Avant le déploiement, Stagebox vérifie chaque appareil cible pour les composants requis. Les appareils ne disposant pas des composants nécessaires (par ex. déployer une planification Cover sur un appareil Switch uniquement) sont ignorés avec un message d'erreur.

##### Vérifier le statut des planifications

1. Sélectionnez les appareils cibles
2. Cliquez sur **📋 Statut**
3. Stagebox interroge chaque appareil et affiche les planifications actuellement installées, y compris leur timespec, méthode et état activé/désactivé

##### Supprimer les planifications des appareils

1. Sélectionnez les appareils cibles
2. Cliquez sur **🗑️ Tout supprimer**
3. Toutes les planifications sur les appareils sélectionnés sont supprimées

> **Avertissement :** « Tout supprimer » supprime **toutes** les planifications des appareils sélectionnés, pas uniquement celles déployées par Stagebox.

<img src="screenshots/54b-schedule-tab-overview.png" width="300" alt="Schedule Tab Overview">
<div style="page-break-before: always;"></div>

#### 2.5.6 Onglet Composants virtuels

Configurer les composants virtuels sur les appareils :

- Interrupteurs virtuels
- Capteurs virtuels
- Composants texte
- Composants nombre

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Device Virtuals Tab">

#### 2.5.7 Onglet Mises à jour FW

Gérer le firmware des appareils :

- Voir la version actuelle
- Vérifier les mises à jour
- Appliquer les mises à jour firmware

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Device FW-Updates Tab">
<div style="page-break-before: always;"></div>

### 2.6 Gestion des scripts

#### 2.6.1 Script Pool (Admin)

Gérer les scripts partagés disponibles pour le déploiement :

1. Allez à la page d'accueil
2. Cliquez sur **📜 Shelly Script Pool** (Admin)
3. Téléchargez des fichiers JavaScript (.js)
4. Supprimez les scripts inutilisés

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Script Pool Dialog">
<div style="page-break-before: always;"></div>

#### 2.6.2 Déploiement de scripts

1. Sélectionnez le(s) appareil(s) cible(s) dans la liste des appareils
2. Allez à l'onglet **Scripts**
3. Sélectionnez la source : **Local** (Script Pool) ou **Bibliothèque GitHub**
4. Choisissez un script
5. Configurez les options :
   - ☑️ Exécuter au démarrage
   - ☑️ Démarrer après le déploiement
6. Cliquez sur **📤 Déployer**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Deploy Script Dialog">

<div style="page-break-before: always;"></div>

### 2.7 Paramètres Expert (Avancé)

> ⚠️ **Avertissement :** Les paramètres Expert permettent la configuration directe du comportement de provisionnement et des paramètres système. Des modifications incorrectes peuvent affecter le provisionnement des appareils. À utiliser avec précaution !

Accès via la section **Expert** → **⚙️ Paramètres du bâtiment** dans la barre latérale de la page du bâtiment.

Le dialogue Paramètres du bâtiment fournit une interface à onglets pour configurer les options avancées.

---

#### 2.7.1 Onglet Provisionnement

Contrôle le comportement du provisionnement Stage 1 (mode AP).

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Expert Provisioning Tab">

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Mode boucle** | Recherche continue de nouveaux appareils. Lorsqu'activé, Stage 1 continue de chercher de nouveaux AP Shelly après chaque provisionnement réussi. Désactiver pour le provisionnement d'un seul appareil. | ☑️ Activé |
| **Désactiver l'AP après provisionnement** | Éteindre le point d'accès WiFi de l'appareil après sa connexion à votre réseau. Recommandé pour la sécurité. | ☑️ Activé |
| **Désactiver le Bluetooth** | Éteindre le Bluetooth sur les appareils provisionnés. Économise l'énergie et réduit la surface d'attaque. | ☑️ Activé |
| **Désactiver le Cloud** | Désactiver la connectivité Shelly Cloud. Les appareils ne seront accessibles que localement. | ☑️ Activé |
| **Désactiver MQTT** | Éteindre le protocole MQTT sur les appareils. Activer si vous utilisez un système domotique avec MQTT. | ☑️ Activé |

---

#### 2.7.2 Onglet OTA & Noms

Configurer le comportement des mises à jour firmware et la gestion des noms conviviaux pendant le Stage 3.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Expert OTA & Names Tab">

**Mises à jour firmware (OTA) :**

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Activer les mises à jour OTA** | Vérifier et optionnellement installer les mises à jour firmware pendant le Stage 3. | ☑️ Activé |
| **Mode de mise à jour** | `Vérifier uniquement` : Signaler les mises à jour disponibles sans les installer. `Vérifier & mettre à jour` : Installer automatiquement les mises à jour disponibles. | Vérifier uniquement |
| **Timeout (secondes)** | Temps d'attente maximum pour les opérations OTA. Augmenter pour les réseaux lents. | 20 |

**Noms conviviaux :**

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Activer les noms conviviaux** | Appliquer les noms de pièce/emplacement aux appareils pendant le Stage 3. Les noms sont stockés dans la configuration de l'appareil. | ☑️ Activé |
| **Compléter les noms manquants** | Générer automatiquement les noms pour les appareils qui n'en ont pas. Utilise le modèle `<Modèle>_<Suffixe-MAC>`. | ☐ Désactivé |

<div style="page-break-before: always;"></div>

#### 2.7.3 Onglet Export

Configurer les paramètres d'export CSV pour les étiquettes d'appareils et les rapports.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Expert Export Tab">

**Délimiteur CSV :**

Choisissez le séparateur de colonnes pour les fichiers CSV exportés :
- **Point-virgule (;)** — Par défaut, fonctionne avec les versions européennes d'Excel
- **Virgule (,)** — Format CSV standard
- **Tabulation** — Pour les valeurs séparées par des tabulations

**Colonnes par défaut :**

Sélectionnez les colonnes qui apparaissent dans les fichiers CSV exportés. Colonnes disponibles :

| Colonne | Description |
|---------|-------------|
| `id` | Adresse MAC de l'appareil (identifiant unique) |
| `ip` | Adresse IP actuelle |
| `hostname` | Nom d'hôte de l'appareil |
| `fw` | Version du firmware |
| `model` | Nom de modèle convivial |
| `hw_model` | ID du modèle matériel |
| `friendly_name` | Nom attribué à l'appareil |
| `room` | Attribution de pièce |
| `location` | Emplacement dans la pièce |
| `assigned_at` | Date de provisionnement |
| `last_seen` | Dernier horodatage de communication |
| `stage3_friendly_status` | Statut d'attribution du nom |
| `stage3_ota_status` | Statut de mise à jour firmware |
| `stage4_status_result` | Résultat de l'étape de configuration |

<div style="page-break-before: always;"></div>

#### 2.7.4 Onglet Carte des modèles

Définir des noms d'affichage personnalisés pour les ID de modèles matériels Shelly.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Expert Model Map Tab">

La carte des modèles traduit les identifiants matériels internes (par ex. `SNSW-001X16EU`) en noms lisibles (par ex. `Shelly Plus 1`).

**Utilisation :**
1. Entrez l'**ID matériel** exactement comme signalé par l'appareil
2. Entrez votre **Nom d'affichage** préféré
3. Cliquez sur **+ Ajouter un modèle** pour ajouter d'autres entrées
4. Cliquez sur **🗑️** pour supprimer une entrée

> **Astuce :** Vérifiez l'interface web ou la réponse API de l'appareil pour trouver la chaîne exacte de l'ID matériel.

<div style="page-break-before: always;"></div>

#### 2.7.5 Onglet Avancé (Éditeur YAML)

Édition directe des fichiers de configuration pour les scénarios avancés.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Expert Advanced Tab">

**Fichiers disponibles :**

| Fichier | Description |
|---------|-------------|
| `config.yaml` | Configuration principale du bâtiment (plages IP, base de données d'appareils, paramètres de provisionnement) |
| `profiles/*.yaml` | Profils de configuration d'appareils pour le Stage 4 |

**Fonctionnalités :**
- Validation de syntaxe (indicateur vert/rouge)
- Sélection de fichier depuis le menu déroulant
- Édition directe du contenu
- Toutes les modifications sont automatiquement sauvegardées avant l'enregistrement

**Indicateur de validation :**
- 🟢 Vert : Syntaxe YAML valide
- 🔴 Rouge : Erreur de syntaxe (détails au survol)

> **Recommandation :** Utilisez les autres onglets pour la configuration normale. N'utilisez l'éditeur YAML que lorsque vous devez modifier des paramètres non exposés dans l'UI, ou pour le dépannage.

<div style="page-break-before: always;"></div>

### 2.8 Maintenance système

#### 2.8.1 Mises à jour Stagebox

Vérifier et installer les mises à jour logicielles de la Stagebox :

1. Allez à la page d'accueil
2. Cliquez sur **📦 Mise à jour Stagebox** (Admin)
3. Les versions actuelle et disponible sont affichées
4. Cliquez sur **⬇️ Installer la mise à jour** si disponible
5. Attendez l'installation et le redémarrage automatique

<img src="screenshots/80-stagebox-update.png" width="450" alt="Stagebox Update Dialog">
<div style="page-break-before: always;"></div>

#### 2.8.2 Mises à jour système

Vérifier et installer les mises à jour du système d'exploitation :

1. Allez à la page d'accueil
2. Cliquez sur **🖥️ Mises à jour système** (Admin)
3. Les mises à jour de sécurité et système sont listées
4. Cliquez sur **⬇️ Installer les mises à jour**
5. Le système peut redémarrer si nécessaire

<img src="screenshots/81-system-updates.png" width="450" alt="System Updates Dialog">

---

<div style="page-break-before: always;"></div>

### 2.9 Rapports & Documentation

Stagebox offre des fonctionnalités complètes de rapport pour la documentation professionnelle d'installation. Les rapports incluent les inventaires d'appareils, les détails de configuration et peuvent être personnalisés avec le branding de l'installateur.

#### 2.9.1 Profil installateur

Le profil installateur contient les informations de votre entreprise qui apparaissent sur tous les rapports générés. C'est un paramètre global partagé entre tous les bâtiments.

**Accès au profil installateur :**

1. Allez à la page d'accueil
2. Cliquez sur **🏢 Profil installateur** (Admin requis)

**Champs disponibles :**

| Champ | Description |
|-------|-------------|
| Nom de l'entreprise | Votre raison sociale |
| Adresse | Adresse postale (multi-lignes possible) |
| Téléphone | Numéro de téléphone de contact |
| E-mail | Adresse e-mail de contact |
| Site web | URL du site web de l'entreprise |
| Logo | Image du logo de l'entreprise (PNG, JPG, max 2 Mo) |

**Directives pour le logo :**
- Taille recommandée : 400×200 pixels ou ratio similaire
- Formats : PNG (fond transparent recommandé) ou JPG
- Taille maximale : 2 Mo
- Le logo apparaît dans l'en-tête des rapports PDF

> **Astuce :** Complétez le profil installateur avant de générer votre premier rapport pour assurer une documentation professionnelle.

<img src="screenshots/90-installer-profile.png" width="450" alt="Installer Profile Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.2 Profil du bâtiment (Informations objet)

Chaque bâtiment peut avoir son propre profil avec des informations spécifiques au client et au projet. Ces données apparaissent dans les rapports générés pour ce bâtiment.

**Accès au profil du bâtiment :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Expert** dans la barre latérale
3. Cliquez sur **⚙️ Paramètres du bâtiment**
4. Sélectionnez l'onglet **Objet**

**Champs disponibles :**

| Champ | Description |
|-------|-------------|
| Nom de l'objet | Nom du projet ou de la propriété (par ex. « Villa Müller ») |
| Nom du client | Nom du client |
| Adresse | Adresse de la propriété (multi-lignes possible) |
| Téléphone de contact | Numéro de téléphone du client |
| E-mail de contact | Adresse e-mail du client |
| Notes | Notes supplémentaires (apparaissent dans les rapports) |

> **Remarque :** Le nom de l'objet est utilisé comme titre du rapport. S'il n'est pas défini, le nom du bâtiment est utilisé à la place.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Building Profile Tab">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Un snapshot capture l'état complet de tous les appareils d'un bâtiment à un moment donné. Les snapshots sont stockés sous forme de paquets ZIP contenant les données des appareils et les fichiers de configuration.

**Création d'un snapshot :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **📸 Snapshots**
4. Attendez la fin du scan

**Gestion des snapshots :**

| Action | Description |
|--------|-------------|
| 📥 Télécharger | Télécharger le paquet ZIP du snapshot |
| 🗑️ Supprimer | Supprimer le snapshot |

**Contenu du ZIP du snapshot :**

Chaque snapshot est stocké sous forme de fichier ZIP contenant :

| Fichier | Description |
|---------|-------------|
| `snapshot.json` | Données complètes du scan des appareils (IP, MAC, config, statut) |
| `installer_profile.json` | Informations de l'entreprise de l'installateur |
| `installer_logo.png` | Logo de l'entreprise (si configuré) |
| `ip_state.json` | Base de données des appareils avec attributions pièce/emplacement |
| `building_profile.json` | Informations objet/client |
| `config.yaml` | Configuration du bâtiment |
| `shelly_model_map.yaml` | Correspondances personnalisées des noms de modèles (si configuré) |
| `scripts/*.js` | Scripts déployés (le cas échéant) |

> **Astuce :** Les snapshots sont des paquets autonomes qui peuvent être utilisés avec des outils de documentation externes ou archivés pour référence future.

**Nettoyage automatique :**

Stagebox conserve automatiquement uniquement les 5 snapshots les plus récents par bâtiment pour économiser l'espace de stockage.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Snapshots Dialog">

<div style="page-break-before: always;"></div>

#### 2.9.4 Générateur de rapports

Générer des rapports d'installation professionnels au format PDF ou Excel.

**Génération d'un rapport :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **📊 Générateur de rapports**
4. Configurez les options du rapport :
   - **Snapshot** : Créer nouveau ou sélectionner un snapshot existant
   - **Langue** : Langue du rapport (DE, EN, FR, IT, NL)
   - **Format** : PDF ou Excel (XLSX)
5. Cliquez sur **Générer**

<img src="screenshots/93-report-generator.png" width="450" alt="Report Generator Dialog">

**Contenu du rapport PDF :**

Le rapport PDF comprend :
- **En-tête** : Logo de l'entreprise, titre du rapport, date de génération
- **Informations objet** : Nom du client, adresse, coordonnées
- **Résumé** : Nombre total d'appareils, pièces et types d'appareils
- **Tableau des appareils** : Inventaire complet avec codes QR

**Colonnes du tableau des appareils :**

| Colonne | Description |
|---------|-------------|
| QR | Code QR lié à l'interface web de l'appareil |
| Pièce | Pièce attribuée |
| Emplacement | Position dans la pièce |
| Nom | Nom convivial de l'appareil |
| Modèle | Type d'appareil |
| IP | Adresse réseau |
| FW | Version du firmware |
| MAC | 6 derniers caractères de l'adresse MAC |
| SWTAK | Indicateurs de fonctionnalités (voir ci-dessous) |

**Indicateurs de fonctionnalités (SWTAK) :**

Chaque appareil indique quelles fonctionnalités sont configurées :

| Indicateur | Signification | Source |
|------------|---------------|--------|
| **S** | Scripts | L'appareil a des scripts installés |
| **W** | Webhooks | L'appareil a des webhooks configurés |
| **T** | Timers | Minuteries auto-on ou auto-off actives |
| **A** | Schedules | Automatisations planifiées configurées |
| **K** | KVS | Entrées Key-Value Store présentes |

Les indicateurs actifs sont mis en évidence, les indicateurs inactifs sont grisés.

**Rapport Excel :**

L'export Excel contient les mêmes informations que le PDF au format tableur :
- Feuille de calcul unique avec tous les appareils
- En-tête avec métadonnées du rapport
- Légende expliquant les indicateurs SWTAK
- Colonnes optimisées pour le filtrage et le tri

> **Astuce :** Utilisez le format Excel lorsque vous devez traiter davantage les données ou créer une documentation personnalisée.

<div style="page-break-before: always;"></div>

#### 2.9.5 Audit de configuration

La fonction Audit compare l'état actuel en direct de tous les appareils avec un snapshot de référence pour détecter les changements de configuration, les nouveaux appareils ou les appareils hors ligne.

**Exécution d'un audit :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **🔍 Lancer l'audit**
4. Sélectionnez un snapshot de référence dans le menu déroulant
5. Cliquez sur **🔍 Démarrer l'audit**

<img src="screenshots/94-audit-setup.png" width="450" alt="Audit Setup Dialog">

Le système effectue un nouveau scan de tous les appareils et les compare au snapshot sélectionné.

**Résultats de l'audit :**

| Statut | Icône | Description |
|--------|-------|-------------|
| OK | ✅ | Appareil inchangé depuis le snapshot |
| Modifié | ⚠️ | Différences de configuration détectées |
| Hors ligne | ❌ | L'appareil était dans le snapshot mais ne répond pas |
| Nouveau | 🆕 | Appareil trouvé qui n'était pas dans le snapshot |

<img src="screenshots/95-audit-results.png" width="500" alt="Audit Results">

**Changements détectés :**

L'audit détecte et signale :
- Changements d'adresse IP
- Changements de nom d'appareil
- Mises à jour de firmware
- Changements de configuration (types d'entrée, paramètres d'interrupteur, paramètres de volet)
- Modifications des paramètres WiFi
- Appareils nouveaux ou manquants

**Cas d'utilisation :**

- **Vérification post-installation** : Confirmer que tous les appareils sont configurés comme documenté
- **Contrôles de maintenance** : Détecter les changements inattendus depuis la dernière visite
- **Dépannage** : Identifier quels paramètres ont été modifiés
- **Documentation de remise** : Vérifier que l'installation correspond à la spécification avant la remise

> **Astuce :** Créez un snapshot après avoir terminé une installation pour l'utiliser comme référence pour les audits futurs.

<div style="page-break-before: always;"></div>

## Annexe

### A. Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| `Escape` | Fermer le dialogue/modal |
| `Enter` | Confirmer le dialogue |

### B. Indicateurs de statut

| Icône | Signification |
|-------|---------------|
| 🟢 (vert) | Appareil en ligne |
| 🔴 (rouge) | Appareil hors ligne |
| S1–S4 | Étape de provisionnement actuelle |
| ⚡ | Mise à jour firmware disponible |

### C. Dépannage

**Impossible d'accéder à la Web-UI :**
- Vérifier la connexion Ethernet
- Vérifier si la Stagebox a une IP (liste DHCP du routeur ou écran OLED)
- Essayer l'adresse IP directement au lieu de .local

**PIN Admin oublié :**
- Maintenir le bouton OLED enfoncé pendant **10+ secondes**
- L'écran affichera « PIN RESET » et « PIN = 0000 »
- Le PIN est maintenant réinitialisé au défaut `0000`
- Se connecter avec `0000` et changer le PIN immédiatement

**Appareils non trouvés au Stage 1 :**
- S'assurer que l'appareil est en mode AP (LED clignotante)
- Rapprocher la Stagebox de l'appareil
- Vérifier la connexion de l'adaptateur WiFi

**Appareils non trouvés au Stage 2 :**
- Vérifier les paramètres de la plage DHCP
- Vérifier si l'appareil est connecté au bon WiFi
- Attendre 30 secondes après le Stage 1

**Stage 4 échoue :**
- Vérifier la compatibilité de l'appareil
- Vérifier qu'un profil existe pour le type d'appareil
- Vérifier que l'appareil est en ligne

**Erreurs de sauvegarde USB :**
- Retirer et réinsérer la clé USB
- Si l'erreur persiste, rafraîchir la page (Ctrl+F5)
- S'assurer que la clé USB est formatée pour Stagebox (Admin → Formater clé USB)

**Génération de rapport lente :**
- Les grandes installations (50+ appareils) peuvent prendre 10–20 secondes
- La génération PDF inclut la création de codes QR pour chaque appareil
- Utiliser le format Excel pour une génération plus rapide sans codes QR

---

*Manuel Stagebox Web-UI — Version 1.1.0*