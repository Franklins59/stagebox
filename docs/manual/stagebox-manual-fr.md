# Manuel d'utilisation Stagebox Web-UI

## Partie 1 : Premiers pas

Ce guide vous accompagne dans la configuration initiale de votre Stagebox et la création de votre premier projet de bâtiment.
  



<img src="screenshots/01-stagebox-picture.png" width="700" alt="Photo du produit">

### 1.1 Connexion de la Stagebox

1. Connectez la Stagebox à votre réseau à l'aide d'un câble Ethernet
2. Branchez l'alimentation électrique
3. Attendez environ 60 secondes pour que le système démarre
4. L'écran OLED à l'avant affichera les informations de connexion

> **Remarque :** La Stagebox nécessite une connexion réseau filaire. Le WiFi est utilisé uniquement pour le provisionnement des appareils Shelly.

<div style="page-break-before: always;"></div>

### 1.2 Utilisation de l'écran OLED

La Stagebox dispose d'un écran OLED intégré qui alterne automatiquement entre plusieurs écrans d'information (toutes les 10 secondes).

**Écran 1 - Splash (Identification principale) :**

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
- Titre "STAGEBOX"
- Adresse IP pour l'accès web
- Suffixe MAC (6 derniers caractères pour l'identification)

**Écran 2 - Info bâtiment :**
- Version actuelle de la Stagebox
- Nom du bâtiment actif

**Écran 3 - État du système :**
- Température et charge CPU
- Température NVMe
- Utilisation RAM et disque

**Écran 4 - Réseau :**
- Adresse IP Ethernet
- Adresse IP WLAN (si connecté)
- Nom d'hôte

**Écran 5 - Horloge :**
- Heure actuelle avec secondes
- Date actuelle

<div style="page-break-before: always;"></div>

**Fonctions du bouton OLED :**

Le bouton sur le boîtier Argon ONE contrôle l'affichage :

| Durée de pression | Action |
|-------------------|--------|
| Pression courte (<2s) | Passer à l'écran suivant |
| Pression longue (2-10s) | Activer/désactiver l'affichage |
| Pression très longue (10s+) | Réinitialiser le PIN Admin à `0000` |

> **Conseil :** Utilisez l'écran Splash ou Réseau pour trouver l'adresse IP nécessaire pour accéder à l'interface Web.

<div style="page-break-before: always;"></div>

### 1.3 Accès à l'interface Web

Trouvez l'adresse IP sur l'écran OLED (écran Splash ou Réseau), puis ouvrez un navigateur web et accédez à :

```
http://<ADRESSE-IP>:5000
```

Par exemple : `http://192.168.1.100:5000`

**Alternative avec le nom d'hôte :**

```
http://stagebox-XXXXXX.local:5000
```

Remplacez `XXXXXX` par le suffixe MAC affiché sur l'écran OLED.

> **Remarque :** Le nom d'hôte `.local` nécessite le support mDNS (Bonjour). S'il ne fonctionne pas, utilisez directement l'adresse IP.

<img src="screenshots/03-greeting-first-access.png" width="450" alt="Page d'accueil - Premier accès">
<div style="page-break-before: always;"></div>

### 1.4 Connexion en tant qu'Admin

Les fonctions administratives sont protégées par un code PIN. Le PIN par défaut est **0000**.

1. Cliquez sur **🔒 Admin** dans la section Admin
2. Entrez le PIN (par défaut : `0000`)
3. Cliquez sur **Confirmer**

Vous êtes maintenant connecté en tant qu'Admin (affiché comme 🔓 Admin).

<img src="screenshots/04-admin-login.png" width="450" alt="Connexion Admin">

> **Recommandation de sécurité :** Changez le PIN par défaut immédiatement après la première connexion (voir section 1.7).
<div style="page-break-before: always;"></div>

### 1.5 Créer votre premier bâtiment

Un "bâtiment" dans Stagebox représente un projet ou un site d'installation. Chaque bâtiment possède sa propre base de données d'appareils, pool d'IP et configuration.

1. Assurez-vous d'être connecté en tant qu'Admin (🔓 Admin visible)
2. Cliquez sur **➕ Nouveau bâtiment**
3. Entrez un nom de bâtiment (ex : `maison_client`)
   - Utilisez uniquement des lettres minuscules, des chiffres et des underscores
   - Les espaces et caractères spéciaux sont automatiquement convertis
4. Cliquez sur **Créer**

<img src="screenshots/05-new-building-dialog.png" width="450" alt="Dialogue Nouveau bâtiment">

Le bâtiment est créé et **s'ouvre automatiquement** avec le dialogue de configuration WiFi.

---

> ⚠️ **CRITIQUE : Configurez correctement les paramètres WiFi !**
>
> Les paramètres WiFi que vous entrez ici déterminent à quel réseau vos appareils Shelly se connecteront. **Des paramètres incorrects rendront les appareils inaccessibles !**
>
> - Vérifiez l'orthographe du SSID (sensible à la casse !)
> - Vérifiez que le mot de passe est correct
> - Assurez-vous que les plages d'IP correspondent à votre réseau réel
>
> Les appareils provisionnés avec de mauvais identifiants WiFi doivent être réinitialisés aux paramètres d'usine et reprovisionnés.

<div style="page-break-before: always;"></div>

### 1.6 Configuration du WiFi et des plages d'IP

Après la création d'un bâtiment, le dialogue **Paramètres du bâtiment** apparaît automatiquement.

<img src="screenshots/07-building-settings.png" width="200" alt="Paramètres du bâtiment">

#### Configuration WiFi

Entrez les identifiants WiFi auxquels les appareils Shelly doivent se connecter :

**WiFi principal (requis) :**
- SSID : Nom de votre réseau (ex : `ReseauMaison`)
- Mot de passe : Votre mot de passe WiFi

**WiFi de secours (optionnel) :**
- Un réseau de secours si le principal n'est pas disponible

<img src="screenshots/08-wifi-settings.png" width="450" alt="Paramètres WiFi">

#### Plages d'adresses IP

Configurez le pool d'IP statiques pour les appareils Shelly :

**Pool Shelly :**
- De : Première IP pour les appareils (ex : `192.168.1.50`)
- À : Dernière IP pour les appareils (ex : `192.168.1.99`)

**Passerelle :**
- Généralement l'IP de votre routeur (ex : `192.168.1.1`)
- Laisser vide pour la détection automatique (.1)

**Plage de scan DHCP (optionnel) :**
- Plage où les nouveaux appareils apparaissent après réinitialisation d'usine
- Laisser vide pour scanner tout le sous-réseau (plus lent)

<img src="screenshots/09-ip-range-settings.png" width="450" alt="Paramètres de plage IP">

> **Avertissement :** Les plages d'IP doivent correspondre à votre réseau réel ! Les appareils seront inaccessibles s'ils sont configurés avec un mauvais sous-réseau.

5. Cliquez sur **💾 Enregistrer**

<div style="page-break-before: always;"></div>

### 1.7 Changer le PIN Admin

Pour changer votre PIN Admin (par défaut `0000`) :

1. Cliquez sur **🔓 Admin** (doit être connecté)
2. Cliquez sur **🔑 Changer PIN**
3. Entrez le nouveau PIN (minimum 4 chiffres)
4. Confirmez le nouveau PIN
5. Cliquez sur **Enregistrer**

<img src="screenshots/10-change-pin-dialog.png" width="300" alt="Dialogue Changer PIN">

> **Important :** Mémorisez ce PIN ! Il protège toutes les fonctions administratives, y compris la suppression de bâtiments et les paramètres système.

### 1.8 Étapes suivantes

Votre Stagebox est maintenant prête pour le provisionnement d'appareils. Continuez vers la Partie 2 pour en savoir plus sur :
- Le provisionnement de nouveaux appareils Shelly (Stage 1-4)
- La gestion des appareils
- La création de sauvegardes

---

<div style="page-break-before: always;"></div>

## Partie 2 : Référence des fonctions

### 2.1 Page d'accueil (Sélection du bâtiment)

La page d'accueil est le point de départ après l'accès à la Stagebox. Elle affiche tous les bâtiments et fournit des fonctions système globales.

<img src="screenshots/20-greeting-page-overview.png" width="450" alt="Aperçu de la page d'accueil">

#### 2.1.1 Liste des bâtiments

La zone centrale affiche tous les bâtiments disponibles sous forme de cartes.

Chaque carte de bâtiment affiche :
- Nom du bâtiment
- Résumé de la plage d'IP
- Nombre d'appareils

**Actions (mode Admin uniquement) :**
- ✏️ Renommer le bâtiment
- 🗑️ Supprimer le bâtiment

<img src="screenshots/21-building-cards.png" width="200" alt="Cartes de bâtiments">

**Sélection d'un bâtiment :**
- Simple clic pour sélectionner
- Double-clic pour ouvrir directement
- Cliquez sur **Ouvrir →** après sélection

#### 2.1.2 Section Système

Située à gauche de la liste des bâtiments :

| Bouton | Fonction | Admin requis |
|--------|----------|--------------|
| 💾 Sauvegarde sur USB | Créer une sauvegarde de tous les bâtiments sur clé USB | Non |
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
| 📜 Pool de scripts Shelly | Gérer les scripts partagés |
| 📂 Restaurer depuis USB | Restaurer les bâtiments depuis une sauvegarde USB |
| 🔌 Formater clé USB | Préparer une clé USB pour les sauvegardes |
| 🔑 Changer PIN | Changer le PIN Admin |
| 📦 Mise à jour Stagebox | Vérifier les mises à jour logicielles |
| 🖥️ Mises à jour système | Vérifier les mises à jour OS |
| 🌐 Langue | Changer la langue de l'interface |
| 🏢 Profil installateur | Configurer les informations de l'entreprise pour les rapports |


#### 2.1.4 Sauvegarde USB

**Créer une sauvegarde :**

1. Insérez une clé USB (tout format)
2. Si non formatée pour Stagebox : Cliquez sur **🔌 Formater clé USB** (Admin)
3. Cliquez sur **💾 Sauvegarde sur USB**
4. Attendez le message de confirmation
5. La clé USB peut maintenant être retirée en toute sécurité

<img src="screenshots/24-usb-format-dialog.png" width="400" alt="Dialogue Format USB">

**Restaurer depuis USB :**

1. Insérez la clé USB contenant les sauvegardes
2. Cliquez sur **📂 Restaurer depuis USB** (Admin)
3. Sélectionnez une sauvegarde dans la liste
4. Choisissez les bâtiments à restaurer
5. Cliquez sur **Restaurer la sélection**

<img src="screenshots/25-usb-restore-dialog.png" width="400" alt="Dialogue Restauration USB">

#### 2.1.5 Exporter/Importer des bâtiments

**Export :**
1. Cliquez sur **📤 Exporter tous les bâtiments** (Admin)
2. Un fichier ZIP contenant toutes les données des bâtiments est téléchargé

**Import :**
1. Cliquez sur **📥 Importer bâtiment(s)** (Admin)
2. Glissez-déposez un fichier ZIP ou cliquez pour sélectionner
3. Choisissez les bâtiments à importer
4. Sélectionnez l'action pour les bâtiments existants (ignorer/écraser)
5. Cliquez sur **Importer la sélection**

<img src="screenshots/26-import-buildings-dialog.png" width="400" alt="Dialogue Importer bâtiments">

<div style="page-break-before: always;"></div>

### 2.2 Page du bâtiment

La page du bâtiment est l'espace de travail principal pour le provisionnement et la gestion des appareils dans un bâtiment spécifique.

<img src="screenshots/30-building-page-overview.png" width="500" alt="Aperçu de la page du bâtiment">

#### Disposition :
- **Barre latérale gauche :** Étapes de provisionnement, filtres, actions, paramètres
- **Zone centrale :** Liste des appareils
- **Barre latérale droite :** Panneaux Stage ou détails de l'appareil, onglets Script, KVS, Webhook et OTA

### 2.3 Barre latérale gauche

#### 2.3.1 En-tête du bâtiment

Affiche le nom du bâtiment actuel. Cliquez pour retourner à la page d'accueil.
<div style="page-break-before: always;"></div>

#### 2.3.2 Étapes de provisionnement

Le pipeline de provisionnement en 4 étapes :

<img src="screenshots/31-provisioning-stages.png" width="180" alt="Étapes de provisionnement">

**S1 - Provisionnement AP :**
- Recherche les appareils Shelly en mode AP (Point d'accès)
- Configure les identifiants WiFi
- Désactive le cloud, BLE et le mode AP

**S2 - Adopt :**
- Scanne le réseau pour les nouveaux appareils (plage DHCP)
- Attribue des IP statiques du pool
- Enregistre les appareils dans la base de données

**S3 - OTA & Noms :**
- Met à jour le firmware vers la dernière version
- Synchronise les noms conviviaux vers les appareils

**S4 - Configurer :**
- Applique les profils d'appareils
- Configure les entrées, interrupteurs, volets, etc.

<div style="page-break-before: always;"></div>

#### 2.3.3 Stage 1 : Provisionnement AP

1. Cliquez sur le bouton **S1**
2. L'adaptateur WiFi de la Stagebox recherche les AP Shelly
3. Les appareils trouvés sont automatiquement configurés, le compteur d'appareils augmente
4. Cliquez sur **⏹ Stop** quand terminé

<img src="screenshots/32-stage1-panel.png" width="450" alt="Panneau Stage 1">

> **Conseil :** Mettez les appareils Shelly en mode AP en maintenant le bouton enfoncé pendant 10+ secondes ou en effectuant une réinitialisation d'usine.

<div style="page-break-before: always;"></div>

#### 2.3.4 Stage 2 : Adopt

1. Cliquez sur le bouton **S2**
2. Cliquez sur **Scanner le réseau**
3. Les nouveaux appareils apparaissent dans la liste
4. Sélectionnez les appareils à adopter ou cliquez sur **Tout adopter**
5. Les appareils reçoivent des IP statiques et sont enregistrés

<img src="screenshots/33-stage2-panel.png" width="300" alt="Panneau Stage 2">

<div style="page-break-before: always;"></div>

#### 2.3.5 Stage 3 : OTA & Noms

1. Cliquez sur le bouton **S3**
2. Les appareils au Stage 2 sont listés
3. Cliquez sur **Exécuter Stage 3** pour :
   - Mettre à jour le firmware (si une version plus récente est disponible)
   - Synchroniser les noms conviviaux de la base de données vers les appareils

<img src="screenshots/34-stage3-panel.png" width="300" alt="Panneau Stage 3">

<div style="page-break-before: always;"></div>

#### 2.3.6 Stage 4 : Configurer

1. Cliquez sur le bouton **S4**
2. Les appareils au Stage 3 sont listés
3. Cliquez sur **Exécuter Stage 4** pour appliquer les profils :
   - Paramètres des interrupteurs (état initial, extinction auto)
   - Paramètres des volets (inverser la direction, limites)
   - Configurations des entrées
   - Actions personnalisées

<img src="screenshots/35-stage4-panel.png" width="300" alt="Panneau Stage 4">

<div style="page-break-before: always;"></div>

#### 2.3.7 Filtres

Filtrez la liste des appareils selon différents critères :

| Filtre | Description |
|--------|-------------|
| Stage | Afficher les appareils à une étape de provisionnement spécifique |
| Pièce | Afficher les appareils dans une pièce spécifique |
| Modèle | Afficher des types d'appareils spécifiques |
| Statut | Appareils en ligne/hors ligne |

<img src="screenshots/36-filter-panel.png" width="200" alt="Panneau Filtres">

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

<img src="screenshots/40-device-list.png" width="500" alt="Liste des appareils">

#### Colonnes :

| Colonne | Description |
|---------|-------------|
| ☑️ | Case à cocher de sélection |
| Statut | En ligne (🟢) / Hors ligne (🔴) |
| Nom | Nom convivial de l'appareil |
| Pièce | Pièce assignée |
| Emplacement | Position dans la pièce |
| Modèle | Type d'appareil |
| IP | Adresse IP actuelle |
| Stage | Étape de provisionnement actuelle (S1-S4) |

#### Sélection :
- Cliquez sur la case à cocher pour sélectionner des appareils individuels
- Cliquez sur la case d'en-tête pour sélectionner tous les visibles
- Maj+clic pour la sélection par plage

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
| Pièce | Assignation de pièce (modifiable) |
| Emplacement | Position dans la pièce (modifiable) |
| MAC | Adresse matérielle |
| IP | Adresse réseau |
| Modèle | Modèle matériel |
| Firmware | Version actuelle |

<img src="screenshots/50-device-info-tab.png" width="300" alt="Onglet Info appareil">

<div style="page-break-before: always;"></div>

#### 2.5.2 Onglet Scripts

Gérer les scripts sur l'appareil sélectionné :

- Voir les scripts installés
- Démarrer/Arrêter les scripts
- Supprimer des scripts
- Déployer de nouveaux scripts

<img src="screenshots/51-device-scripts-tab.png" width="300" alt="Onglet Scripts appareil">

#### 2.5.3 Onglet KVS

Voir et modifier les entrées Key-Value Store :

- Valeurs système (lecture seule)
- Valeurs utilisateur (modifiables)
- Ajouter de nouvelles entrées
- Supprimer des entrées

<img src="screenshots/52-device-kvs-tab.png" width="300" alt="Onglet KVS appareil">
<div style="page-break-before: always;"></div>

#### 2.5.4 Onglet Webhooks

Configurer les webhooks de l'appareil :

- Voir les webhooks existants
- Ajouter de nouveaux webhooks
- Modifier les URLs et conditions
- Supprimer des webhooks

<img src="screenshots/53-device-webhooks-tab.png" width="300" alt="Onglet Webhooks appareil">

#### 2.5.5 Onglet Planifications

Gérer les tâches planifiées :

- Voir les planifications existantes
- Ajouter des automatisations basées sur le temps
- Activer/désactiver les planifications
- Supprimer des planifications

<img src="screenshots/54-device-schedules-tab.png" width="300" alt="Onglet Planifications appareil">

#### 2.5.6 Onglet Composants virtuels

Configurer les composants virtuels sur les appareils :

- Interrupteurs virtuels
- Capteurs virtuels
- Composants texte
- Composants numériques

<img src="screenshots/55-device-virtuals-tab.png" width="300" alt="Onglet Virtuels appareil">

#### 2.5.7 Onglet Mises à jour FW

Gérer le firmware de l'appareil :

- Voir la version actuelle
- Vérifier les mises à jour
- Appliquer les mises à jour firmware

<img src="screenshots/56-device-fw-updates-tab.png" width="300" alt="Onglet Mises à jour FW appareil">
<div style="page-break-before: always;"></div>

### 2.6 Gestion des scripts

#### 2.6.1 Pool de scripts (Admin)

Gérer les scripts partagés disponibles pour le déploiement :

1. Allez à la page d'accueil
2. Cliquez sur **📜 Pool de scripts Shelly** (Admin)
3. Téléchargez des fichiers JavaScript (.js)
4. Supprimez les scripts inutilisés

<img src="screenshots/60-script-pool-dialog.png" width="300" alt="Dialogue Pool de scripts">
<div style="page-break-before: always;"></div>

#### 2.6.2 Déployer des scripts

1. Sélectionnez le(s) appareil(s) cible dans la liste
2. Allez à l'onglet **Scripts**
3. Sélectionnez la source : **Local** (Pool de scripts) ou **Bibliothèque GitHub**
4. Choisissez un script
5. Configurez les options :
   - ☑️ Exécuter au démarrage
   - ☑️ Démarrer après déploiement
6. Cliquez sur **📤 Déployer**

<img src="screenshots/61-deploy-script-dialog.png" width="300" alt="Dialogue Déployer script">

<div style="page-break-before: always;"></div>

### 2.7 Paramètres Expert (Avancé)

> ⚠️ **Avertissement :** Les paramètres Expert permettent la configuration directe du comportement de provisionnement et des paramètres système. Des modifications incorrectes peuvent affecter le provisionnement des appareils. À utiliser avec précaution !

Accès via la section **Expert** → **⚙️ Paramètres du bâtiment** dans la barre latérale de la page du bâtiment.

Le dialogue Paramètres du bâtiment fournit une interface à onglets pour configurer les options avancées.

---

#### 2.7.1 Onglet Provisionnement

Contrôle le comportement du provisionnement Stage 1 (mode AP).

<img src="screenshots/70-expert-provisioning-tab.png" width="450" alt="Onglet Expert Provisionnement">

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Mode boucle** | Rechercher continuellement de nouveaux appareils. Lorsqu'activé, Stage 1 continue de rechercher de nouveaux AP Shelly après chaque provisionnement réussi. Désactiver pour le provisionnement d'un seul appareil. | ☑️ Activé |
| **Désactiver AP après provisionnement** | Désactiver le point d'accès WiFi de l'appareil après connexion à votre réseau. Recommandé pour la sécurité. | ☑️ Activé |
| **Désactiver Bluetooth** | Désactiver le Bluetooth sur les appareils provisionnés. Économise l'énergie et réduit la surface d'attaque. | ☑️ Activé |
| **Désactiver Cloud** | Désactiver la connectivité Shelly Cloud. Les appareils ne seront accessibles que localement. | ☑️ Activé |
| **Désactiver MQTT** | Désactiver le protocole MQTT sur les appareils. Activer si vous utilisez un système domotique avec MQTT. | ☑️ Activé |

---

#### 2.7.2 Onglet OTA & Noms

Configurer le comportement des mises à jour firmware et la gestion des noms conviviaux pendant Stage 3.

<img src="screenshots/71-expert-ota-tab.png" width="450" alt="Onglet Expert OTA">

**Mises à jour firmware (OTA) :**

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Activer mises à jour OTA** | Vérifier et optionnellement installer les mises à jour firmware pendant Stage 3. | ☑️ Activé |
| **Mode de mise à jour** | `Vérifier seulement` : Signaler les mises à jour disponibles sans installer. `Vérifier & Mettre à jour` : Installer automatiquement les mises à jour disponibles. | Vérifier seulement |
| **Timeout (secondes)** | Temps d'attente maximum pour les opérations OTA. Augmenter pour les réseaux lents. | 20 |

**Noms conviviaux :**

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| **Activer noms conviviaux** | Appliquer les noms de pièce/emplacement aux appareils pendant Stage 3. Les noms sont stockés dans la configuration de l'appareil. | ☑️ Activé |
| **Compléter noms manquants** | Générer automatiquement des noms pour les appareils sans assignation. Utilise le modèle `<Modèle>_<Suffixe-MAC>`. | ☐ Désactivé |

<div style="page-break-before: always;"></div>

#### 2.7.3 Onglet Export

Configurer les paramètres d'export CSV pour les étiquettes d'appareils et les rapports.

<img src="screenshots/72-expert-export-tab.png" width="450" alt="Onglet Expert Export">

**Délimiteur CSV :**

Choisissez le séparateur de colonnes pour les fichiers CSV exportés :
- **Point-virgule (;)** - Par défaut, fonctionne avec les versions Excel européennes
- **Virgule (,)** - Format CSV standard
- **Tabulation** - Pour les valeurs séparées par tabulation

**Colonnes par défaut :**

Sélectionnez les colonnes qui apparaissent dans les fichiers CSV exportés. Colonnes disponibles :

| Colonne | Description |
|---------|-------------|
| `id` | Adresse MAC de l'appareil (identifiant unique) |
| `ip` | Adresse IP actuelle |
| `hostname` | Nom d'hôte de l'appareil |
| `fw` | Version firmware |
| `model` | Nom de modèle convivial |
| `hw_model` | ID du modèle matériel |
| `friendly_name` | Nom d'appareil assigné |
| `room` | Assignation de pièce |
| `location` | Emplacement dans la pièce |
| `assigned_at` | Date de provisionnement de l'appareil |
| `last_seen` | Horodatage de la dernière communication |
| `stage3_friendly_status` | Statut d'assignation de nom |
| `stage3_ota_status` | Statut de mise à jour firmware |
| `stage4_status_result` | Résultat de l'étape de configuration |

<div style="page-break-before: always;"></div>

#### 2.7.4 Onglet Model Map

Définir des noms d'affichage personnalisés pour les ID de modèles matériels Shelly.

<img src="screenshots/73-expert-modelmap-tab.png" width="450" alt="Onglet Expert Model Map">

La Model Map traduit les identifiants matériels internes (ex : `SNSW-001X16EU`) en noms lisibles (ex : `Shelly Plus 1`).

**Utilisation :**
1. Entrez l'**ID matériel** exactement comme rapporté par l'appareil
2. Entrez votre **Nom d'affichage** préféré
3. Cliquez sur **+ Ajouter modèle** pour ajouter d'autres entrées
4. Cliquez sur **🗑️** pour supprimer une entrée

> **Conseil :** Vérifiez l'interface web de l'appareil ou la réponse API pour trouver la chaîne exacte de l'ID matériel.

<div style="page-break-before: always;"></div>

#### 2.7.5 Onglet Avancé (Éditeur YAML)

Édition directe des fichiers de configuration pour les scénarios avancés.

<img src="screenshots/74-expert-advanced-tab.png" width="450" alt="Onglet Expert Avancé">

**Fichiers disponibles :**

| Fichier | Description |
|---------|-------------|
| `config.yaml` | Configuration principale du bâtiment (plages IP, base de données d'appareils, paramètres de provisionnement) |
| `profiles/*.yaml` | Profils de configuration d'appareils pour Stage 4 |

**Fonctionnalités :**
- Validation de syntaxe (indicateur vert/rouge)
- Sélectionner un fichier dans le menu déroulant
- Éditer le contenu directement
- Toutes les modifications sont automatiquement sauvegardées avant enregistrement

**Indicateur de validation :**
- 🟢 Vert : Syntaxe YAML valide
- 🔴 Rouge : Erreur de syntaxe (survoler pour les détails)

> **Recommandation :** Utilisez les autres onglets pour la configuration normale. N'utilisez l'éditeur YAML que lorsque vous devez modifier des paramètres non exposés dans l'interface, ou pour le dépannage.

<div style="page-break-before: always;"></div>

### 2.8 Maintenance système

#### 2.8.1 Mises à jour Stagebox

Vérifier et installer les mises à jour logicielles Stagebox :

1. Allez à la page d'accueil
2. Cliquez sur **📦 Mise à jour Stagebox** (Admin)
3. Les versions actuelle et disponible sont affichées
4. Cliquez sur **⬇️ Installer la mise à jour** si disponible
5. Attendez l'installation et le redémarrage automatique

<img src="screenshots/80-stagebox-update.png" width="450" alt="Dialogue Mise à jour Stagebox">
<div style="page-break-before: always;"></div>

#### 2.8.2 Mises à jour système

Vérifier et installer les mises à jour du système d'exploitation :

1. Allez à la page d'accueil
2. Cliquez sur **🖥️ Mises à jour système** (Admin)
3. Les mises à jour de sécurité et système sont listées
4. Cliquez sur **⬇️ Installer les mises à jour**
5. Le système peut redémarrer si nécessaire

<img src="screenshots/81-system-updates.png" width="450" alt="Dialogue Mises à jour système">

---

<div style="page-break-before: always;"></div>

### 2.9 Rapports & Documentation

Stagebox fournit des fonctionnalités de rapport complètes pour la documentation professionnelle d'installation. Les rapports incluent les inventaires d'appareils, les détails de configuration, et peuvent être personnalisés avec le branding de l'installateur.

#### 2.9.1 Profil installateur

Le profil installateur contient les informations de votre entreprise qui apparaissent sur tous les rapports générés. C'est un paramètre global partagé entre tous les bâtiments.

**Accès au profil installateur :**

1. Allez à la page d'accueil
2. Cliquez sur **🏢 Profil installateur** (Admin requis)

**Champs disponibles :**

| Champ | Description |
|-------|-------------|
| Nom de l'entreprise | Nom de votre entreprise ou commerce |
| Adresse | Adresse postale (multiligne supporté) |
| Téléphone | Numéro de téléphone de contact |
| E-mail | Adresse e-mail de contact |
| Site web | URL du site web de l'entreprise |
| Logo | Image du logo de l'entreprise (PNG, JPG, max 2Mo) |

**Directives pour le logo :**
- Taille recommandée : 400×200 pixels ou ratio similaire
- Formats : PNG (fond transparent recommandé) ou JPG
- Taille maximale : 2Mo
- Le logo apparaît dans l'en-tête des rapports PDF

> **Conseil :** Complétez le profil installateur avant de générer votre premier rapport pour assurer une documentation d'aspect professionnel.

<img src="screenshots/90-installer-profile.png" width="450" alt="Dialogue Profil installateur">

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
| Nom de l'objet | Nom du projet ou de la propriété (ex : "Villa Müller") |
| Nom du client | Nom du client |
| Adresse | Adresse de la propriété (multiligne supporté) |
| Téléphone de contact | Numéro de téléphone du client |
| E-mail de contact | Adresse e-mail du client |
| Notes | Notes supplémentaires (apparaissent dans les rapports) |

> **Remarque :** Le nom de l'objet est utilisé comme titre du rapport. S'il n'est pas défini, le nom du bâtiment est utilisé à la place.

<img src="screenshots/91-building-profile-tab.png" width="450" alt="Onglet Profil du bâtiment">

<div style="page-break-before: always;"></div>

#### 2.9.3 Snapshots

Un snapshot capture l'état complet de tous les appareils d'un bâtiment à un moment donné. Les snapshots sont stockés sous forme de bundles ZIP contenant les données des appareils et les fichiers de configuration.

**Créer un snapshot :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **📸 Snapshots**
4. Attendez la fin du scan

**Gestion des snapshots :**

| Action | Description |
|--------|-------------|
| 📥 Télécharger | Télécharger le bundle ZIP du snapshot |
| 🗑️ Supprimer | Supprimer le snapshot |

**Contenu du ZIP du snapshot :**

Chaque snapshot est stocké dans un fichier ZIP contenant :

| Fichier | Description |
|---------|-------------|
| `snapshot.json` | Données complètes du scan d'appareils (IP, MAC, config, statut) |
| `installer_profile.json` | Informations de l'entreprise de l'installateur |
| `installer_logo.png` | Logo de l'entreprise (si configuré) |
| `ip_state.json` | Base de données d'appareils avec assignations pièce/emplacement |
| `building_profile.json` | Informations objet/client |
| `config.yaml` | Configuration du bâtiment |
| `shelly_model_map.yaml` | Mappages de noms de modèles personnalisés (si configuré) |
| `scripts/*.js` | Scripts déployés (le cas échéant) |

> **Conseil :** Les snapshots sont des bundles autonomes qui peuvent être utilisés avec des outils de documentation externes ou archivés pour référence future.

**Nettoyage automatique :**

Stagebox conserve automatiquement uniquement les 5 snapshots les plus récents par bâtiment pour économiser l'espace de stockage.

<img src="screenshots/92-snapshots-dialog.png" width="450" alt="Dialogue Snapshots">

<div style="page-break-before: always;"></div>

#### 2.9.4 Générateur de rapports

Générer des rapports d'installation professionnels au format PDF ou Excel.

**Générer un rapport :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **📊 Générateur de rapports**
4. Configurez les options du rapport :
   - **Snapshot** : Créer nouveau ou sélectionner existant
   - **Langue** : Langue du rapport (DE, EN, FR, IT, NL)
   - **Format** : PDF ou Excel (XLSX)
5. Cliquez sur **Générer**

<img src="screenshots/93-report-generator.png" width="450" alt="Dialogue Générateur de rapports">

**Contenu du rapport PDF :**

Le rapport PDF inclut :
- **En-tête** : Logo de l'entreprise, titre du rapport, date de génération
- **Informations objet** : Nom du client, adresse, coordonnées
- **Résumé** : Total des appareils, pièces et types d'appareils
- **Tableau des appareils** : Inventaire complet avec codes QR

**Colonnes du tableau des appareils :**

| Colonne | Description |
|---------|-------------|
| QR | Code QR liant à l'interface web de l'appareil |
| Pièce | Pièce assignée |
| Emplacement | Position dans la pièce |
| Nom | Nom convivial de l'appareil |
| Modèle | Type d'appareil |
| IP | Adresse réseau |
| FW | Version firmware |
| MAC | 6 derniers caractères de l'adresse MAC |
| SWTAK | Indicateurs de fonctionnalités (voir ci-dessous) |

**Indicateurs de fonctionnalités (SWTAK) :**

Chaque appareil affiche les fonctionnalités configurées :

| Indicateur | Signification | Source |
|------------|---------------|--------|
| **S** | Scripts | L'appareil a des scripts installés |
| **W** | Webhooks | L'appareil a des webhooks configurés |
| **T** | Timers | Timers auto-on ou auto-off actifs |
| **A** | Planifications | Automatisations planifiées configurées |
| **K** | KVS | Entrées Key-Value Store présentes |

Les indicateurs actifs sont mis en évidence, les indicateurs inactifs sont grisés.

**Rapport Excel :**

L'export Excel contient les mêmes informations que le PDF au format tableur :
- Feuille unique avec tous les appareils
- En-tête avec métadonnées du rapport
- Légende expliquant les indicateurs SWTAK
- Colonnes optimisées pour le filtrage et le tri

> **Conseil :** Utilisez le format Excel quand vous devez traiter les données ou créer une documentation personnalisée.

<div style="page-break-before: always;"></div>

#### 2.9.5 Audit de configuration

La fonction Audit compare l'état live actuel de tous les appareils avec un snapshot de référence pour détecter les changements de configuration, les nouveaux appareils ou les appareils hors ligne.

**Exécuter un audit :**

1. Ouvrez la page du bâtiment
2. Allez à la section **Audit** dans la barre latérale
3. Cliquez sur **🔍 Exécuter l'audit**
4. Sélectionnez un snapshot de référence dans le menu déroulant
5. Cliquez sur **🔍 Démarrer l'audit**

<img src="screenshots/94-audit-setup.png" width="450" alt="Dialogue Configuration de l'audit">

Le système effectuera un nouveau scan de tous les appareils et les comparera au snapshot sélectionné.

**Résultats de l'audit :**

| Statut | Icône | Description |
|--------|-------|-------------|
| OK | ✅ | Appareil inchangé depuis le snapshot |
| Modifié | ⚠️ | Différences de configuration détectées |
| Hors ligne | ❌ | L'appareil était dans le snapshot mais ne répond pas |
| Nouveau | 🆕 | Appareil trouvé qui n'était pas dans le snapshot |

<img src="screenshots/95-audit-results.png" width="500" alt="Résultats de l'audit">

**Changements détectés :**

L'audit détecte et rapporte :
- Changements d'adresse IP
- Changements de nom d'appareil
- Mises à jour firmware
- Changements de configuration (types d'entrée, paramètres d'interrupteur, paramètres de volet)
- Modifications des paramètres WiFi
- Appareils nouveaux ou manquants

**Cas d'utilisation :**

- **Vérification post-installation** : Confirmer que tous les appareils sont configurés comme documenté
- **Contrôles de maintenance** : Détecter les changements inattendus depuis la dernière visite
- **Dépannage** : Identifier quels paramètres ont été modifiés
- **Documentation de remise** : Vérifier que l'installation correspond aux spécifications avant remise

> **Conseil :** Créez un snapshot après avoir terminé une installation pour l'utiliser comme référence pour les audits futurs.

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
| S1-S4 | Étape de provisionnement actuelle |
| ⚡ | Mise à jour firmware disponible |

### C. Dépannage

**Impossible d'accéder à l'interface Web :**
- Vérifier la connexion Ethernet
- Vérifier si la Stagebox a une IP (liste DHCP du routeur ou écran OLED)
- Essayer l'adresse IP directement au lieu de .local

**PIN Admin oublié :**
- Maintenez le bouton OLED pendant **10+ secondes**
- L'écran affichera "PIN RESET" et "PIN = 0000"
- Le PIN est maintenant réinitialisé à `0000` par défaut
- Connectez-vous avec `0000` et changez le PIN immédiatement

**Appareils non trouvés au Stage 1 :**
- S'assurer que l'appareil est en mode AP (LED clignotante)
- Rapprocher la Stagebox de l'appareil
- Vérifier la connexion de l'adaptateur WiFi

**Appareils non trouvés au Stage 2 :**
- Vérifier les paramètres de plage DHCP
- Vérifier si l'appareil est connecté au bon WiFi
- Attendre 30 secondes après le Stage 1

**Le Stage 4 échoue :**
- Vérifier la compatibilité de l'appareil
- Vérifier qu'un profil existe pour le type d'appareil
- Vérifier que l'appareil est en ligne

**Erreurs de sauvegarde USB :**
- Retirer et réinsérer la clé USB
- Si l'erreur persiste, rafraîchir la page (Ctrl+F5)
- S'assurer que la clé USB est formatée pour Stagebox (Admin → Formater clé USB)

**Génération de rapport lente :**
- Les grandes installations (50+ appareils) peuvent prendre 10-20 secondes
- La génération PDF inclut la création de codes QR pour chaque appareil
- Utiliser le format Excel pour une génération plus rapide sans codes QR

---

*Manuel d'utilisation Stagebox Web-UI - Version 1.5*