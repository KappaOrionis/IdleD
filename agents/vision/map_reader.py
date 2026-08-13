import re
from typing import Dict, Any, Optional

class MapHUDReader:
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur d'En-tête de Carte Dofus Unity.
    Analyse l'en-tête visuel de la carte pour extraire:
    - Zone & Sous-zone (ex: "Baie de Sufokia (Sufokia)")
    - Coordonnées de la tuile [x, y] (ex: [12, 27])
    - Niveau de la zone (ex: 10)
    """
    def __init__(self):
        # Regex pour capturer les coordonnées et le niveau (ex: "12, 27 - Niveau 10")
        self.coords_level_pattern = re.compile(r"(-?\d+)\s*,\s*(-?\d+)\s*-\s*Niveau\s*(\d+)", re.IGNORECASE)
        # Regex pour capturer le nom de zone (ex: "Baie de Sufokia (Sufokia)")
        self.zone_pattern = re.compile(r"^([A-Za-zÀ-ÿ\s'-]+(?:\([A-Za-zÀ-ÿ\s'-]+\))?)")

    def parse_hud_text(self, text_line_1: str, text_line_2: str) -> Dict[str, Any]:
        """
        Analyse deux lignes de texte extraites de l'HUD pour en tirer les données structurées.
        """
        zone_name = text_line_1.strip() if text_line_1 else "Inconnue"
        pos_x, pos_y, level = 0, 0, 1

        match = self.coords_level_pattern.search(text_line_2)
        if match:
            pos_x = int(match.group(1))
            pos_y = int(match.group(2))
            level = int(match.group(3))

        return {
            "zone_name": zone_name,
            "tile_coords": [pos_x, pos_y],
            "area_level": level,
            "raw_text": f"{text_line_1} | {text_line_2}"
        }

if __name__ == "__main__":
    reader = MapHUDReader()
    # Test avec l'exemple exact de la capture Dofus Unity :
    # Line 1: "Baie de Sufokia (Sufokia)"
    # Line 2: "12, 27 - Niveau 10"
    result = reader.parse_hud_text("Baie de Sufokia (Sufokia)", "12, 27 - Niveau 10")
    print(f"[La Noxine MapReader] Détection réussie: {result}")
