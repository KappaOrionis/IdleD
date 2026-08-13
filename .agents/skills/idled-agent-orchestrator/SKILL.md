---
name: idled-agent-orchestrator
description: Skill de gestion et d'orchestration des 4 micro-agents autonomes (Cadran, Noxine, Cerveau, Scaphandre) pour IdleD.
---

# IdleD Agent Orchestration Skill

Ce skill fournit les directives opérationnelles pour orchestrer et maintenir l'architecture multi-agents hors-ligne du système IdleD.

## Rôles des Agents

1. **Le Cadran (Superviseur Rust)**
   - Maintient l'état courant de l'application via `src-tauri/src/fsm.rs`.
   - Intercepte les interruptions matérielles et les flèches directionnelles via `src-tauri/src/hotkeys.rs`.
   - Communique avec le harnais Python via le pont IPC (`src-tauri/src/ipc.rs`).

2. **La Noxine (Perception Visuelle)**
   - Située dans `agents/vision/`.
   - Exécute le matching de templates visuels (`template_matcher.py`) et la capture d'écran CUDA (`screen_capture.py`).

3. **Le Cerveau (Agent Tactique & Décisionnel)**
   - Situé dans `agents/brain/`.
   - Calcule les trajectoires via l'algorithme A* (`pathfinding.py`) et évalue la menace et la ligne de vue (`combat_logic.py`).

4. **Le Scaphandre (Agent d'Exécution Motrice)**
   - Situé dans `agents/motor/`.
   - Exécute les déplacements de souris non-linéaires (`bezier_mouse.py`) et les frappes clavier humanisées (`keyboard_sim.py`).

## Protocole de Sécurité & Humanisation
- **Click Radius** : Tout clic généré par Le Scaphandre doit comporter un offset aléatoire.
- **Délai Variable** : Insérer des micro-pauses aléatoires entre l'analyse de La Noxine et l'action du Scaphandre.
- **Urgence Instantanée** : La touche globale `F12` doit immédiatement faire basculer la FSM du Cadran en `EmergencyStop`.
