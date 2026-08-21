import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any

class GameScreenLayout:
    """
    Agent de Perception Visuelle (La Noxine) - Gestionnaire Centralisé du Layout d'Écran Dofus Unity.
    
    Découpe et masque avec précision les régions d'interface utilisateur pour isoler 
    exclusivement la surface de terrain isométrique jouable (minerais, plots soleils, monstres, PNJ).
    """
    def __init__(
        self,
        quest_panel_open: bool = True,
        minimap_open: bool = True,
        chat_height_ratio: float = 0.25,
    ):
        self.quest_panel_open = quest_panel_open
        self.minimap_open = minimap_open
        self.chat_height_ratio = chat_height_ratio

    @staticmethod
    def get_hud_map_crop(frame: np.ndarray) -> np.ndarray:
        """
        Extrait la zone ROI de l'en-tête de carte (Zone, Coordonnées, Niveau) en haut à gauche.
        """
        h, w = frame.shape[:2]
        crop_w = int(w * 0.26)
        crop_h = int(h * 0.085)
        return frame[0:crop_h, 0:crop_w]

    def get_playable_area_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Génère un masque binaire 2D (uint8) de la taille de la frame où :
        - 255 = Zone de jeu active (Terrain isométrique jouable)
        - 0 = Zone d'interface utilisateur masquée (HUD, Quêtes, Chat, Sorts, Mini-carte)
        """
        h, w = frame.shape[:2]
        mask = np.ones((h, w), dtype=np.uint8) * 255

        # 1. Neutralisation de l'en-tête supérieur & barre de niveau
        mask[0:int(h * 0.05), :] = 0
        mask[0:int(h * 0.085), 0:int(w * 0.26)] = 0  # HUD Carte

        # 2. Neutralisation du volet latéral gauche des quêtes (si ouvert)
        if self.quest_panel_open:
            mask[int(h * 0.085):int(h * 0.75), 0:int(w * 0.145)] = 0

        # 3. Neutralisation du panneau de chat (Bas Gauche)
        chat_top = int(h * (1.0 - self.chat_height_ratio))
        mask[chat_top:, 0:int(w * 0.26)] = 0

        # 4. Neutralisation de la bulle de PV (Cœur) et barre des sorts (Bas Centre)
        mask[int(h * 0.76):, int(w * 0.26):int(w * 0.68)] = 0

        # 5. Neutralisation du cadre de la Mini-Carte (Bas Droite, si ouverte)
        if self.minimap_open:
            mask[int(h * 0.74):, int(w * 0.68):] = 0

        # 6. Neutralisation de la colonne verticale d'icônes à droite (Bord Droit)
        mask[:, int(w * 0.97):] = 0

        return mask

    def apply_to_mask(self, binary_mask: np.ndarray) -> np.ndarray:
        """
        Applique le masque de découpage directement sur un masque binaire existant (in-place bitwise AND).
        """
        h, w = binary_mask.shape[:2]
        area_mask = self.get_playable_area_mask(binary_mask)
        return cv2.bitwise_and(binary_mask, binary_mask, mask=area_mask)
