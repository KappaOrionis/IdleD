# ADR-0001: Architecture Hybride Multi-Agents Hors-Ligne (Rust + Python + Tauri)

## Status

Accepted

## Context

Le projet **IdleD** est une plateforme d'orchestration et de supervision logicielle agissant comme une surcouche (overlay) locale pour le client de jeu Dofus Unity. Elle nécessite :
- Une interception matérielle instantanée et sécurisée des raccourcis globaux et des touches directionnelles sous Windows.
- Un traitement vidéo et de vision par ordinateur en temps réel (Template Matching avec accélération GPU CUDA).
- Une interface de supervision réactive, transparente (always-on-top) et légère intégrant le rendu cartographique Leaflet.js.
- Une étanchéité totale aux requêtes réseau cloud (principe Offline-First).

## Decision Drivers

- **Performance et Sécurité Matérielle** : Faible empreinte mémoire, interception fiable des entrées OS sans blocage.
- **Flexibilité de la Vision par Ordinateur** : Exploitation de l'écosystème OpenCV et CUDA en Python.
- **Réactivité UI & Overlay Transparent** : Rendu cartographique Web (Leaflet) fluide embarqué dans une fenêtre native légère.
- **Souveraineté des Données** : Exécution 100% locale déconnectée.

## Considered Options

### Option 1: Architecture Hybride Rust (Superviseur) + Python (Agents Vision/Motricité) + Tauri (UI)

- **Pros** : Rust garantit la sécurité des threads et l'interception OS bas niveau ; Python offre un accès direct et mature à OpenCV/CUDA ; Tauri fournit un binaire natif ultraléger avec rendu WebView transparent.
- **Cons** : Nécessite la gestion d'un pont IPC (JSON-RPC) inter-processus.

### Option 2: Tout-en-Python (PyQt/PySide + OpenCV + PyAutoGUI)

- **Pros** : Stack monolithique en un seul langage.
- **Cons** : Performance UI inférieure, surconsommation mémoire, difficultés à créer un overlay transparent fluide always-on-top et à gérer les hooks globaux bas niveau en multi-threading sans GIL blocking.

### Option 3: Tout-en-Electron + Node.js (C++ Bindings)

- **Pros** : Écosystème web riche.
- **Cons** : Empreinte mémoire massive (Chromium + Node), intégration OpenCV plus lourde à maintenir.

## Decision

Nous adoptons **l'Option 1 : Architecture Hybride Rust + Python + Tauri**.

- **Rust / Tauri** : Maintient le Superviseur (Machine à États Finis `fsm.rs`), l'interception matérielle (`hotkeys.rs`), la fenêtre overlay transparent et le pont IPC (`ipc.rs`).
- **Python Harness** : Micro-services d'Agents découplés (`La Noxine` pour la vision, `Le Cerveau` pour la décision/pathfinding A*, `Le Scaphandre` pour les mouvements de souris Bézier et frappes OS).
- **SQLite** : Base de données locale déconnectée pour l'encyclopédie et le Grimoire.

## Rationale

1. **Isolation des responsabilités** : Le découpage en 4 agents spécialisés prévient les blocages UI et garantit que l'agent motrice ne clique que sur instruction validée.
2. **Performance** : Le traitement OpenCV/CUDA s'exécute séparément sans ralentir la FSM Rust du superviseur.
3. **Sécurité Anti-Détection** : La simulation motrice humanisée (Bézier + dispersion) est confinée dans un micro-service dédié configurable.

## Consequences

### Positive

- Empreinte mémoire minimale du backend et de l'overlay UI.
- Extensibilité des profils tactiques et algorithmes de routage sans modifier le Superviseur Rust.
- Fonctionnement 100% autonome et déconnecté (Offline-First).

### Negative

- Nécessite la maintenance du protocole IPC Rust <-> Python.
- Déploiement nécessitant un environnement Python local préconfiguré avec OpenCV.

## Related Decisions

- ADR-0002: Stratégie de persistance SQLite et schéma du Grimoire (à venir).
