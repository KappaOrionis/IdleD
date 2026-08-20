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
        sleep_fn: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Exécute la macro complète de minage sur la carte courante.
        
        :param detected_nodes: Liste des filons détectés [{x, y, ...}]
        :param selected_ores: Minerais sélectionnés (si None, utilise self.selected_ores, défaut ['fer'])
        :param move_cursor_fn: Fonction de déplacement souris Le Scaphandre
        :param read_tooltip_fn: Fonction de lecture infobulle La Noxine
        :param click_fn: Fonction de clic de récolte Le Scaphandre
        :param sleep_fn: Fonction de temporisation (défaut time.sleep)
        """
        _sleep = sleep_fn if sleep_fn is not None else time.sleep
        target_ores = [self._normalize_ore_name(o) for o in (selected_ores or self.selected_ores)]
        if not target_ores:
            target_ores = ["fer"]

        ordered_nodes = self.sort_nodes_by_proximity(detected_nodes)
        
        inspected = 0
        mined = []
        skipped = []

        for node in ordered_nodes:
            nx, ny = node.get("x", 0), node.get("y", 0)
            inspected += 1

            # 1. Survol physique humanisé vers le filon
            if move_cursor_fn:
                move_cursor_fn(nx, ny)

            # 2. Pause physiologique pour apparition de l'infobulle (100 - 150ms)
            _sleep(0.12)

            # 3. Analyse du Tooltip par La Noxine
            tooltip_data = {}
            if read_tooltip_fn:
                try:
                    tooltip_data = read_tooltip_fn() or {}
                except Exception:
                    tooltip_data = {}

            ore_type = self._normalize_ore_name(tooltip_data.get("resource_name", node.get("ore_type", "fer")))
            status = tooltip_data.get("status", "available").lower()

            # 4. Décision de récolte
            is_target = ore_type in target_ores
            is_available = status not in ["depleted", "epuise", "épuisé", "cooldown"]

            if is_target and is_available:
                if click_fn:
                    click_fn()
                mined.append({
                    "x": nx,
                    "y": ny,
                    "ore_type": ore_type,
                    "status": "mined"
                })
                # Temps de pioche / animation
                _sleep(0.3)
            else:
                reason = "not_selected" if not is_target else "depleted"
                skipped.append({
                    "x": nx,
                    "y": ny,
                    "ore_type": ore_type,
                    "reason": reason
                })

        return {
            "success": True,
            "target_ores": target_ores,
            "inspected_count": inspected,
            "mined_count": len(mined),
            "mined_nodes": mined,
            "skipped_count": len(skipped),
            "skipped_nodes": skipped
        }

if __name__ == "__main__":
    routine = RoomMinerRoutine(default_selected_ores=["fer"])
    dummy_nodes = [
        {"x": 300, "y": 400, "ore_type": "fer"},
        {"x": 700, "y": 450, "ore_type": "bronze"},
        {"x": 400, "y": 200, "ore_type": "fer"}
    ]
    report = routine.execute_room_mining(dummy_nodes, selected_ores=["fer"])
    print("[Macro Minage] Rapport d'exécution ->", report)
