# IdleD Project Agent Rules & Directives

## Workspace Architecture Directives

1. **Isolation des Responsabilités Multi-Agents**
   - **Superviseur Rust (Le Cadran)** : Gère exclusivement la Machine à États (FSM), les raccourcis globaux (Hotkeys) et le dispatching IPC. Il ne doit pas intégrer de logique métier de jeu.
   - **Perception Visuelle (La Noxine)** : Doit rester 100% aveugle à la décision. Elle renvoie uniquement des coordonnées, des indices de confiance et des détections brutes.
   - **Décision & Tactique (Le Cerveau)** : Calcule la stratégie, le routage A* et les séquences de combat sans interagir directement avec les périphériques OS.
   - **Exécution Motrice (Le Scaphandre)** : Seul composant autorisé à émettre des clics et des frappes clavier au niveau du système d'exploitation. Doit toujours appliquer les variations humanisées (Bézier, dispersion, délais aléatoires).

2. **Offline-First & Security**
   - Aucune dépendance externe ni appel réseau d'API cloud n'est toléré dans le code de production.
   - Les données statiques de jeu résident dans SQLite (`data/databases/encyclopedia.db`).
