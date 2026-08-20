# IdleD - Plateforme de Supervision & Automation Dofus Unity (Multi-Agents)

IdleD est une plateforme d'orchestration et de supervision logicielle sous forme d'overlay "Always-on-top" local, conçue pour piloter le client **Dofus Unity**. Elle déploie une architecture multi-agents autonomes et hors-ligne (Offline-First).

---

## 📚 Documentation & Références

Les guides d'architecture, spécifications du produit et inventaires de vision sont centralisés dans le dossier [`docs/`](file:///c:/Users/janvi/LocalRepository/IdleD/docs) :

* 📘 **[Spécifications Produit (PRD.md)](file:///c:/Users/janvi/LocalRepository/IdleD/PRD.md)** : Vision globale du produit, architecture 4-agents et principes offline-first.
* 📷 **[Inventaire des Captures & Ressources (docs/resource_screenshots_inventory.md)](file:///c:/Users/janvi/LocalRepository/IdleD/docs/resource_screenshots_inventory.md)** : Suivi détaillé des captures visuelles à fournir par métier (Mineur, Bûcheron, Paysan, Alchimiste, Pêcheur) et statut des détecteurs visuels de **La Noxine**.

---

## 🏗️ Architecture Multi-Agents

1. **Superviseur Rust (Le Cadran)** : Gère la Machine à États (FSM), les raccourcis globaux (Hotkeys) et l'IPC.
2. **Perception Visuelle (La Noxine)** : Détecteurs visuels OpenCV/HSV (Sun Nodes, Gisements de Cuivre, En-tête HUD).
3. **Décision & Tactique (Le Cerveau)** : Calcul d'itinéraire A*, circuits de récolte et séquences tactiques.
4. **Exécution Motrice (Le Scaphandre)** : Génération de clics Bézier humanisés et simulation clavier au niveau OS.

---

## 🚀 Lancement Rapide

Pour lancer la plateforme :
```bash
.\run\run.bat
```
Option **[1]** pour lancer le Superviseur Tauri / StreamDeck.
Option **[3]** pour exécuter la suite de tests complète (`pytest` + `cargo test`).
