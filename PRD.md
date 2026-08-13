# Product Requirements Document (PRD) : IdleD

1. Vision et Objectifs de l'Application
### 1.1 Description du Produit (Le "Quoi")
IdleD est une plateforme d'orchestration et de supervision logicielle agissant comme une surcouche (overlay) locale spécialement conçue pour piloter le client **Dofus Unity**. Elle déploie une architecture multi-agents hors-ligne chargée de percevoir l'environnement visuel du jeu, de prendre des décisions de routage ou de combat, et d'exécuter des actions motrices (clics humanisés, frappes clavier) directement au niveau du système d'exploitation.

Le système se comporte comme une interface de commandement déléguée : l'utilisateur définit des objectifs (jalons de progression, circuits de récolte, profils tactiques), et le réseau d'agents autonomes se charge de l'exécution mécanique et visuelle sur la carte du jeu, de manière totalement indépendante de toute infrastructure cloud.

1.2 Objectif Principal (Le "Pourquoi")
L'objectif d'IdleD est d'automatiser intelligemment les phases de progression répétitives sur Dofus Unity pour maximiser l'efficience des sessions de jeu, tout en garantissant une insaisissabilité maximale face aux systèmes anti-triche.

Le projet répond à trois impératifs majeurs :

Délégation Tactique et Logistique : Transformer l'expérience de jeu sur Dofus Unity : l'utilisateur passe du statut d'exécutant manuel (cliqueur) à celui de superviseur stratégique, gérant des flux de récolte et des routines de combat complexes tout en optimisant son temps.

Souveraineté et Sécurité (Offline-First) : Garantir que 100% de la capture vidéo, du traitement de la vision par ordinateur et de la prise de décision tactique s'effectue localement, sans aucune compromission des données ou dépendance à des API externes.

Contrôle Hybride (Human-in-the-Loop) : Maintenir un équilibre parfait entre autonomie et contrôle manuel. L'outil doit permettre à l'utilisateur d'interrompre instantanément l'essaim d'agents ou de reprendre la main sur les déplacements du personnage sur les tuiles adjacentes (via les touches directionnelles du clavier) sans friction, simulant ainsi l'imprévisibilité et la fluidité d'un véritable comportement humain.

---

## 2. Spécifications Fonctionnelles (Features)

### 2.1 Interface de Supervision (La Ruche)

* **Overlay "Always-on-top" :** Fenêtre de contrôle réactive superposée au client Dofus Unity.
* **Tableau de Bord Central :** Affichage de l'état actuel de la machine à états (Navigation, Récolte, Combat, Pause).
* **Contrôles Globaux et Arrêt d'Urgence :** Boutons d'exécution (Play, Pause, Stop) liés à des raccourcis clavier globaux (Global Hotkeys) pour des interruptions matérielles instantanées.

### 2.2 Navigation et Déplacement Manuel par Touches Directionnelles

* **Déplacement sur Tuiles Adjacentes par Flèches Directionnelles :** Capacité d'utiliser directement les touches directionnelles du clavier (Flèche Haut, Flèche Bas, Flèche Gauche, Flèche Droite) pour déplacer instantanément le personnage vers la tuile ou la carte adjacente sur Dofus Unity. L'application intercepte la frappe clavier au niveau OS et l'Agent d'Exécution (Le Scaphandre) génère un clic humanisé sur le bord d'écran ou le plot de transition correspondant à la direction demandée.
* **Validation Visuelle :** Confirmation par l'Agent de Perception (La Noxine) de la fin du chargement de la tuile ou de la carte adjacente avant d'autoriser une nouvelle action ou transition.

### 2.3 Module de Cartographie Interactive (Map Visualizer)

* **Rendu Visuel :** Affichage interactif des tuiles de la carte du jeu (Pan & Zoom).
* **Sélecteur d'Itinéraire :** Création de circuits par sélection de tuiles (Clic point par point ou sélection de zone).
* **Affichage Contextuel (Tooltips) :** Survol des tuiles pour afficher les métadonnées (types de monstres, niveaux, ressources, points d'intérêt).

### 2.4 Moteur de Routage Multi-Modal

* **Évaluation des Trajets :** Calcul du chemin le plus rapide ou économique via l'algorithme A* ou Dijkstra pondéré.
* **Réseau de Transport :** Intégration des Zaaps, Zaapis, et potions pour optimiser les déplacements à travers le Monde des Douze.

### 2.5 Module d'Expertise Métier et Combat (Le Grimoire)

* **Base de Données des Sorts :** Connaissance des coûts en PA, portées, et lignes de vue pour optimiser les séquences d'attaque (profils de combat configurables).
* **Séquenceur de Jalons (Milestones) :** Sous-système capable d'ingérer une checklist stricte d'objectifs (leveling, récoltes précises, donjons) pour une exécution autonome.
* **Évaluateur de Menace :** Analyse des caractéristiques des monstres présents sur la tuile pour autoriser ou interdire l'engagement du combat.

### 2.6 Simulation Motrice et Saisie (Humanisation)

* **Déplacements de Souris :** Mouvements non linéaires via la génération de courbes de Bézier simulant le poignet humain.
* **Ciblage et Clics :** Variation aléatoire du rayon de clic (Click Radius) autour du centre de la cible. Gestion des clics gauches, droits, et maintiens (glisser-déposer).
* **Saisie Clavier Intégrale :** Capacité du système à générer des frappes clavier pour utiliser les raccourcis de sorts (1, 2, 3...), saisir du texte dans le chat, ou entrer des prix exacts dans les Hôtels de Vente.
* **Cadence Aléatoire :** Délais d'exécution (Sleep) variables entre l'identification visuelle et l'action mécanique.

---

## 3. Organisation Agentique (Harnais)

L'architecture repose sur un modèle multi-agents où les responsabilités sont strictement isolées pour garantir réactivité et sécurité matérielle.

1. **L'Agent Superviseur (Le Cadran) :** Cerveau central géré par le backend. Il maintient la Machine à États Finis (FSM) et orchestre la distribution des tâches. Il gère l'écoute des Global Hotkeys (dont les touches directionnelles).
2. **L'Agent de Perception Visuelle (La Noxine) :** Exécution en boucle fermée pour capturer l'écran en temps réel. Effectue le *Template Matching* et renvoie uniquement des coordonnées et des indices de confiance, sans prendre de décision.
3. **L'Agent Tactique et Décisionnel (Le Cerveau) :** Moteur d'arbitrage logique. Calcule le chemin de récolte, évalue les Lignes de Vue (LoS), et détermine la séquence d'actions optimale en interrogeant le Grimoire.
4. **L'Agent d'Exécution Motrice (Le Scaphandre) :** Effecteur matériel final. Reçoit les ordres de l'Agent Décisionnel ou du Superviseur (lors de l'utilisation des touches directionnelles), génère les courbes de déplacement et envoie les signaux de clic ou de frappe clavier directement au système d'exploitation.

---

## 4. Stack Technique Recommandée

L'environnement est optimisé pour une exécution fluide sous Windows, tirant parti de l'accélération matérielle pour la vision par ordinateur tout en maintenant une architecture locale.

* **Frontend (Interface & Cartographie) :** `Tauri` + `Leaflet.js` pour un exécutable léger, transparent, et des performances natives sur la gestion de la carte.
* **Backend (Superviseur & OS Control) :** `Rust`. Assure la gestion bas niveau, les threads sécurisés, et l'interception matérielle infaillible des raccourcis clavier et touches directionnelles.
* **Moteur de Vision (Agents) :** `Python` avec `OpenCV`. Intégration de l'accélération CUDA pour exploiter la carte graphique (NVIDIA RTX) lors du traitement en temps réel des flux vidéo et du *Template Matching*.
* **Base de Données Locale :** `SQLite`. Hébergement déconnecté des métadonnées (Grimoire, réseau de transport, encyclopédie) garantissant des requêtes ultra-rapides sans dépendance cloud.

---

idled-app/
│
├── src/                        # 1. FRONTEND (Interface Utilisateur)
│   ├── components/             # Composants UI (Overlay, boutons, checklists)
│   ├── map_visualizer/         # Moteur Leaflet.js pour le rendu cartographique
│   ├── styles/                 # CSS/Tailwind (Design minimaliste de la Ruche)
│   └── main.js                 # Point d'entrée de l'interface
│
├── src-tauri/                  # 2. BACKEND (Superviseur & Machine à États)
│   ├── src/
│   │   ├── main.rs             # Point d'entrée Rust
│   │   ├── fsm.rs              # Logique de la Machine à États Finis (Superviseur)
│   │   ├── hotkeys.rs          # Interception matérielle (Touches directionnelles, arrêts d'urgence)
│   │   └── ipc.rs              # Pont de communication (IPC) avec les agents Python
│   └── tauri.conf.json         # Configuration de la fenêtre (always-on-top, transparence)
│
├── agents/                     # 3. HARNAIS AGENTIQUE (Micro-services Python)
│   ├── vision/                 # L'Agent de Perception (La Noxine)
│   │   ├── template_matcher.py # Script OpenCV d'analyse d'écran
│   │   └── screen_capture.py   # Capture vidéo optimisée CUDA
│   ├── brain/                  # L'Agent Tactique et Décisionnel (Le Cerveau)
│   │   ├── pathfinding.py      # Algorithme A* et routage multi-modal
│   │   └── combat_logic.py     # Évaluation des menaces et Lignes de Vue (LoS)
│   ├── motor/                  # L'Agent d'Exécution (Le Scaphandre)
│   │   ├── bezier_mouse.py     # Génération de mouvements de souris humanisés
│   │   └── keyboard_sim.py     # Simulation de frappes clavier OS-level
│   └── requirements.txt        # Dépendances Python (OpenCV, PyAutoGUI, etc.)
│
├── data/                       # 4. DONNÉES STATIQUES DU JEU (Read-Only)
│   ├── templates/              # Assets visuels pour OpenCV (sprites de blé, interface)
│   ├── tilesets/               # Tuiles de la carte classées par zoom (Z/X/Y) pour Leaflet
│   └── databases/              # Base de données locale
│       └── encyclopedia.db     # SQLite (Réseau Zaap, Grimoire des sorts, Métadonnées monstres)
│
├── config/                     # 5. DONNÉES UTILISATEUR & VAULT (Git-ignored)
│   ├── .env                    # Variables d'environnement locales
│   ├── routes/                 # Fichiers JSON des circuits générés par l'utilisateur
│   └── tactics/                # Profils personnalisés (builds, checklists de jalons)
│
└── logs/                       # 6. TÉLÉMÉTRIE LOCALE
    ├── execution.log           # Journal d'activité du Superviseur
    └── vision_errors/          # Captures d'écran sauvegardées lors d'échecs de détection