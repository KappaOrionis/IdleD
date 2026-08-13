import re
from typing import Dict, Any, Optional

class MapHUDReader:
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur d'En-tête de Carte Dofus Unity.
    Analyse l'en-tête visuel de la carte pour extraire:
    - Zone & Sous-zone (ex: "Baie de Sufokia (Sufokia)")
    - Coordonnées de la tuile [x, y] (ex: [12, 27])
    - Niveau de la zone (ex: 10)
    - Statut de détection (is_detected, error_message)
    """
    def __init__(self):
        self.coords_level_pattern = re.compile(r"(-?\d+)\s*,\s*(-?\d+)\s*-\s*Niveau\s*(\d+)", re.IGNORECASE)
        self.zone_pattern = re.compile(r"^([A-Za-zÀ-ÿ\s'-]+(?:\([A-Za-zÀ-ÿ\s'-]+\))?)")

    def parse_hud_text(self, text_line_1: Optional[str], text_line_2: Optional[str]) -> Dict[str, Any]:
        """
        Analyse deux lignes de texte extraites de l'HUD pour en tirer les données structurées.
        Si la détection échoue (texte vide ou format non reconnu), signale is_detected = False.
        """
        if not text_line_1 or not text_line_2:
            return {
                "is_detected": False,
                "zone_name": "Détection impossible",
                "tile_coords": [None, None],
                "area_level": None,
                "error_message": "Fenêtre masquée, fermée ou chargement de carte en cours",
                "raw_text": ""
            }

        zone_name = text_line_1.strip()
        match = self.coords_level_pattern.search(text_line_2)

        if not match:
            return {
                "is_detected": False,
                "zone_name": zone_name if zone_name else "Détection impossible",
                "tile_coords": [None, None],
                "area_level": None,
                "error_message": "En-tête HUD non reconnu ou carte en cours de chargement",
                "raw_text": f"{text_line_1} | {text_line_2}"
            }

        pos_x = int(match.group(1))
        pos_y = int(match.group(2))
        level = int(match.group(3))

        return {
            "is_detected": True,
            "zone_name": zone_name,
            "tile_coords": [pos_x, pos_y],
            "area_level": level,
            "error_message": None,
            "raw_text": f"{text_line_1} | {text_line_2}"
        }

if __name__ == "__main__":
    reader = MapHUDReader()
    valid = reader.parse_hud_text("Baie de Sufokia (Sufokia)", "12, 27 - Niveau 10")
    invalid = reader.parse_hud_text("", "")
    print(f"[La Noxine MapReader] Détection valide: {valid}")
    print(f"[La Noxine MapReader] Détection impossible: {invalid}")
