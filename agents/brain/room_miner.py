import time
import math
from typing import List, Dict, Any, Optional, Callable

class RoomMinerRoutine:
    """
    Agent Tactique et Décisionnel (Le Cerveau) - Macro de Minage & Inspection de Salle.
    
    Orchestre l'inspection complète de la carte courante :
    1. Récupère les gisements détectés par La Noxine (OreDetector).
    2. Ordonne les filons par proximité (Bézier / TSP).
    3. Survole chaque filon avec Le Scaphandre et vérifie le statut/type via l'infobulle.
    4. Récolte tous les minerais correspondant aux critères sélectionnés (par défaut: ['fer']).
    """
    
    # Dictionnaire de normalisation des noms de minerais
    ORE_NAME_MAP = {
        "fer": "fer",
        "iron": "fer",
        "iron_ore": "fer",
        "cuivre": "cuivre",
        "copper": "cuivre",
        "copper_ore": "cuivre",
        "bronze": "bronze",
        "bronze_ore": "bronze",
        "kobalte": "kobalte",
        "cobalt": "kobalte",
        "manganese": "manganese",
        "etain": "etain",
        "tin": "etain",
        "argent": "argent",
        "silver": "argent",
        "bauxite": "bauxite",
        "or": "or",
        "gold": "or",
        "dolomite": "dolomite",
        "silicate": "silicate",
        "obsidienne": "obsidienne",
        "ecume_mer": "ecume_mer",
        "aquamarine": "aquamarine",
        "orichalque": "orichalque"
    }

    def __init__(self, default_selected_ores: Optional[List[str]] = None):
        if default_selected_ores is None:
            self.selected_ores = ["fer"]
        else:
            self.selected_ores = [self._normalize_ore_name(o) for o in default_selected_ores]

    def _normalize_ore_name(self, name: str) -> str:
        """Normalise un nom de minerai en clé minuscule standard."""
        cleaned = name.lower().strip().replace(" ", "_")
        return self.ORE_NAME_MAP.get(cleaned, cleaned)

    def sort_nodes_by_proximity(self, nodes: List[Dict[str, Any]], start_pos: tuple = (960, 540)) -> List[Dict[str, Any]]:
        """
        Ordonne la liste des nœuds de minerai par ordre de proximité (Nearest Neighbor / TSP)
        pour minimiser les mouvements de souris et assurer un balayage humain fluide.
        """
        if not nodes:
            return []

        remaining = list(nodes)
        ordered = []
        current_pos = start_pos

        while remaining:
            best_idx = 0
            best_dist = float('inf')
            for idx, node in enumerate(remaining):
                nx, ny = node.get("x", 0), node.get("y", 0)
                dist = math.hypot(nx - current_pos[0], ny - current_pos[1])
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

            nearest = remaining.pop(best_idx)
            ordered.append(nearest)
            current_pos = (nearest.get("x", 0), nearest.get("y", 0))

        return ordered

    def execute_room_mining(
        self,
        detected_nodes: List[Dict[str, Any]],
        selected_ores: Optional[List[str]] = None,
        move_cursor_fn: Optional[Callable[[int, int], None]] = None,
        read_tooltip_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        click_fn: Optional[Callable[[], None]] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        speed_multiplier: float = 1.0,
        log_fn: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Exécute la macro de minage et d'inspection sur les filons identifiés.
        
        :param detected_nodes: Liste des filons détectés [{x, y, ...}]
        :param selected_ores: Minerais sélectionnés (si None, utilise self.selected_ores)
        :param move_cursor_fn: Fonction de déplacement souris Le Scaphandre
        :param read_tooltip_fn: Fonction de lecture infobulle La Noxine
        :param click_fn: Fonction de clic de récolte Le Scaphandre
        :param sleep_fn: Fonction de temporisation
        :param speed_multiplier: Facteur de vitesse (1.0 = normal, 0.5 = mode DEBUG ralenti par 2)
        :param log_fn: Fonction de journalisation d'événements
        """
        _sleep = sleep_fn if sleep_fn is not None else time.sleep
        _log = log_fn if log_fn is not None else print
        
        # En mode DEBUG (vitesse / 2), les temporisations sont doublées
        delay_scale = 1.0 / max(0.1, speed_multiplier)
        
        target_ores = [self._normalize_ore_name(o) for o in (selected_ores or self.selected_ores)]
        if not target_ores:
            target_ores = ["fer"]

        ordered_nodes = self.sort_nodes_by_proximity(detected_nodes)
        
        inspected = 0
        mined = []
        skipped = []

        _log(f"[Le Cerveau - Minage] Début inspection de {len(ordered_nodes)} filons (Vitesse: {speed_multiplier}x)...")

        for idx, node in enumerate(ordered_nodes, 1):
            nx, ny = node.get("x", 0), node.get("y", 0)
            inspected += 1

            # Étape 4.A : Survol physique humanisé vers le filon
            _log(f"[Étape 4 - Survol] [{idx}/{len(ordered_nodes)}] Déplacement vers [{nx}, {ny}]...")
            if move_cursor_fn:
                move_cursor_fn(nx, ny)

            # Étape 4.B : Pause pour affichage de l'infobulle (120ms standard, 240ms en debug /2)
            _sleep(0.12 * delay_scale)

            # Étape 4.C : Analyse et classification de l'infobulle (La Noxine)
            tooltip_data = {}
            if read_tooltip_fn:
                try:
                    tooltip_data = read_tooltip_fn() or {}
                except Exception as e:
                    _log(f"[Étape 4 - Tooltip] Erreur lecture infobulle : {e}")
                    tooltip_data = {}

            from agents.vision.ore_detector import OreDetector
            classification = OreDetector.classify_ore_tooltip(tooltip_data)
            ore_type = self._normalize_ore_name(classification.get("ore_type", node.get("ore_type", "fer")))
            state = classification.get("state", "minable") # 'minable', 'non_minable', 'epuise'

            _log(f"[Étape 4 - Classification] Filon #{idx} : {ore_type.upper()} -> État: {state.upper()} ({classification.get('reason', '')})")

            # Étape 5 : Récolte / Minage si minable et sélectionné
            is_target = ore_type in target_ores
            is_minable = (state == "minable")

            if is_target and is_minable:
                _log(f"[Étape 5 - Récolte] Clic de minage sur {ore_type} [{nx}, {ny}]...")
                if click_fn:
                    click_fn()
                mined.append({
                    "x": nx,
                    "y": ny,
                    "ore_type": ore_type,
                    "status": "mined"
                })
                # Pause d'animation de pioche (300ms standard, 600ms en debug /2)
                _sleep(0.30 * delay_scale)
            else:
                reason = "non_selectionne" if not is_target else state
                _log(f"[Étape 5 - Ignoré] Filon {ore_type} ignoré (Raison: {reason})")
                skipped.append({
                    "x": nx,
                    "y": ny,
                    "ore_type": ore_type,
                    "state": state,
                    "reason": reason
                })

        report = {
            "success": True,
            "speed_multiplier": speed_multiplier,
            "target_ores": target_ores,
            "inspected_count": inspected,
            "mined_count": len(mined),
            "mined_nodes": mined,
            "skipped_count": len(skipped),
            "skipped_nodes": skipped
        }
        _log(f"[Le Cerveau - Minage] Rapport final : {len(mined)} minés, {len(skipped)} ignorés.")
        return report

    def execute_full_mining_cycle(
        self,
        capture_frame_fn: Callable[[], Any],
        press_key_fn: Callable[[str], None],
        selected_ores: Optional[List[str]] = None,
        move_cursor_fn: Optional[Callable[[int, int], None]] = None,
        read_tooltip_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        click_fn: Optional[Callable[[], None]] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        speed_multiplier: float = 1.0,
        log_fn: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Exécute le cycle intégral de minage en 5 étapes séquentielles :
        1. Snapshot initial de l'écran (sans surbrillance)
        2. Appui sur la touche 'Y' + Snapshot avec surbrillance
        3. Identification & segmentation différentielle des filons
        4. Passage de la souris (Bézier) & classification infobulle (épuisé, non minable, minable)
        5. Minage du filon (clic gauche si minable et sélectionné)
        """
        _sleep = sleep_fn if sleep_fn is not None else time.sleep
        _log = log_fn if log_fn is not None else print
        delay_scale = 1.0 / max(0.1, speed_multiplier)

        _log(f"=== [CYCLE DE MINAGE - VITESSE {speed_multiplier}x] ===")

        # --- ÉTAPE 1 : Snapshot initial ---
        _log("[Étape 1] Capture du Snapshot initial de l'écran (sans surbrillance)...")
        frame_normal = capture_frame_fn()
        _sleep(0.05 * delay_scale)

        # --- ÉTAPE 2 : Appui touche 'Y' & Snapshot surbrillance ---
        _log("[Étape 2] Activation de la surbrillance (Touche 'Y') et capture de la frame surbrillance...")
        press_key_fn('y')
        _sleep(0.15 * delay_scale) # Stabilisation du halo lumineux
        frame_highlight = capture_frame_fn()

        # --- ÉTAPE 3 : Identification différentielle des zones ---
        _log("[Étape 3] Analyse différentielle et segmentation des zones de filons...")
        from agents.vision.ore_detector import OreDetector
        detector = OreDetector()
        detection_result = detector.detect_from_differential_frames(frame_normal, frame_highlight)
        detected_nodes = detection_result.get("nodes", [])
        _log(f"[Étape 3] {len(detected_nodes)} filon(s) identifié(s) dans la zone jouable.")

        if not detected_nodes:
            _log("[Étape 3] Aucun gisement détecté sur la carte courante.")
            return {
                "success": True,
                "speed_multiplier": speed_multiplier,
                "inspected_count": 0,
                "mined_count": 0,
                "mined_nodes": [],
                "skipped_count": 0,
                "skipped_nodes": []
            }

        # --- ÉTAPES 4 & 5 : Survol, classification infobulle et récolte ---
        return self.execute_room_mining(
            detected_nodes=detected_nodes,
            selected_ores=selected_ores,
            move_cursor_fn=move_cursor_fn,
            read_tooltip_fn=read_tooltip_fn,
            click_fn=click_fn,
            sleep_fn=sleep_fn,
            speed_multiplier=speed_multiplier,
            log_fn=log_fn
        )

if __name__ == "__main__":
    routine = RoomMinerRoutine(default_selected_ores=["fer"])
    dummy_nodes = [
        {"x": 300, "y": 400, "ore_type": "fer"},
        {"x": 700, "y": 450, "ore_type": "cuivre"}
    ]
    report = routine.execute_room_mining(dummy_nodes, selected_ores=["fer"], speed_multiplier=0.5)
    print("[Macro Minage DEBUG 0.5x] Rapport ->", report)
