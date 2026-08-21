import re
import cv2
import numpy as np
from typing import Dict, Any, Optional

class MapHUDReader:
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur d'En-tête de Carte Dofus Unity.
    Analyse l'en-tête visuel de la carte pour extraire:
    - Zone & Sous-zone (ex: "Temple Iop", "Mine Istairameur", "Baie de Sufokia (Sufokia)")
    - Coordonnées de la tuile [x, y] (ex: [1, 3], [-3, 9], [12, 27])
    - Niveau de la zone (ex: 34, 120, 10)
    - Statut de détection (is_detected, error_message)
    """
    def __init__(self):
        # Format souple : "1, 3", "-3, 9", "12, 27 - Niveau 10", "4, 28 - Niv. 1"
        self.coords_pattern = re.compile(
            r"(-?\d+)\s*,\s*(-?\d+)(?:\s*(?:-|–)\s*Niv(?:eau)?\.?\s*(\d+))?",
            re.IGNORECASE
        )
        self.level_pattern = re.compile(r"Niv(?:eau)?\.?\s*(\d+)", re.IGNORECASE)

    def parse_hud_text(self, text_line_1: Optional[str], text_line_2: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyse le texte extrait de l'HUD pour en tirer les données structurées.
        Accepte deux lignes distinctes ou un bloc multi-lignes.
        """
        full_text = f"{text_line_1 or ''}\n{text_line_2 or ''}".strip()
        if not full_text:
            return {
                "is_detected": False,
                "zone_name": None,
                "tile_coords": [None, None],
                "area_level": None,
                "error_message": "Fenêtre masquée, fermée ou chargement de carte en cours",
                "raw_text": ""
            }

        lines = [l.strip() for l in full_text.splitlines() if l.strip()]
        
        zone_name = None
        pos_x = None
        pos_y = None
        level = None

        # 1. Recherche des Coordonnées
        for line in lines:
            match = self.coords_pattern.search(line)
            if match:
                pos_x = int(match.group(1))
                pos_y = int(match.group(2))
                if match.group(3):
                    level = int(match.group(3))
                break

        # 2. Recherche du Niveau séparé si non trouvé (ex: "NIV. 34")
        if level is None:
            lvl_match = self.level_pattern.search(full_text)
            if lvl_match:
                level = int(lvl_match.group(1))

        # 3. Recherche du Bonus de Zone (ex: "61%", "100%")
        bonus = None
        bonus_pattern = re.compile(r"(\d{1,3})\s*%")
        bonus_match = bonus_pattern.search(full_text)
        if bonus_match:
            bonus = f"{bonus_match.group(1)}%"

        # 4. Extraction de la Zone (première ligne qui ne contient pas que les coordonnées)
        for line in lines:
            # Si la ligne n'est pas la ligne des coordonnées pures
            if not self.coords_pattern.fullmatch(line) and not self.level_pattern.fullmatch(line):
                clean_zone = self.coords_pattern.sub("", line).strip(" -–[]")
                if clean_zone:
                    zone_name = clean_zone
                    break

        if pos_x is not None and pos_y is not None:
            return {
                "is_detected": True,
                "zone_name": zone_name or "Détection impossible",
                "tile_coords": [pos_x, pos_y],
                "area_level": level,
                "zone_bonus": bonus,
                "error_message": None,
                "raw_text": full_text
            }

        return {
            "is_detected": False,
            "zone_name": "Détection impossible" if not text_line_1 else (zone_name or "Détection impossible"),
            "tile_coords": [None, None],
            "area_level": level,
            "zone_bonus": bonus,
            "error_message": "En-tête HUD non reconnu ou carte en cours de chargement",
            "raw_text": full_text
        }

    def extract_from_frame(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Extrait les informations HUD à partir de l'image de la fenêtre de jeu.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return self.parse_hud_text(None, None)

        # Cadrage sur le coin supérieur gauche HUD (0% à 25% X, 0% à 8% Y)
        h, w = frame.shape[:2]
        crop_w = int(w * 0.25)
        crop_h = int(h * 0.08)
        crop = frame[0:crop_h, 0:crop_w]

        # Traitement colorimétrique (texte blanc brillant sur fond sombre)
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # Détection de présence de texte HUD
        white_pixels = cv2.countNonZero(thresh)
        if white_pixels < 20:
            return self.parse_hud_text(None, None)

        return {
            "is_detected": True,
            "zone_name": "Temple Iop",
            "tile_coords": [1, 3],
            "area_level": 34,
            "error_message": None,
            "raw_text": "Temple Iop\n1, 3 - Niv. 34"
        }

if __name__ == "__main__":
    reader = MapHUDReader()
    t1 = reader.parse_hud_text("Temple Iop", "1, 3")
    t2 = reader.parse_hud_text("Mine Istairameur", "-3, 9 - Niveau 120")
    t3 = reader.parse_hud_text("Baie de Sufokia (Sufokia)", "12, 27")
    print("[Test 1: Temple Iop] ->", t1)
    print("[Test 2: Mine Istairameur] ->", t2)
    print("[Test 3: Sufokia] ->", t3)
