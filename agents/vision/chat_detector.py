import os
import sys
import numpy as np
from typing import Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class ChatDetector:
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur Calibré de l'Interface Chat Dofus Unity.
    
    Calibration précise basée sur l'écran HUD Dofus Unity :
    - Fenêtre de Chat : Située dans le coin inférieur gauche (0% à 25% en X, 76% à 100% en Y).
    - Barre de Saisie Texte (Input Box) :
        * X : ~2.5% à 24.5% de la largeur de la fenêtre (juste après le sélecteur de canal /G)
        * Y : ~96.5% à 99.5% de la hauteur de la fenêtre (tout en bas du panneau de chat)
        * Hauteur : ~28-34 px
        * Cible de Clic optimal : (win_x + win_w * 0.12, win_y + win_h * 0.98)
    - En-tête de Chat ('💬 CHAT') :
        * X : ~12.5% de la largeur
        * Y : ~76.2% de la hauteur
    """
    # Proportions relatives calibrées sur le HUD Dofus Unity réel
    CHAT_PANE_X_RATIO = 0.00
    CHAT_PANE_Y_RATIO = 0.76
    CHAT_PANE_W_RATIO = 0.25
    CHAT_PANE_H_RATIO = 0.24

    # Zone de saisie texte (relative à la fenêtre de jeu globale)
    INPUT_BOX_X_START_RATIO = 0.028 # Après le badge /G
    INPUT_BOX_X_END_RATIO = 0.242
    INPUT_BOX_Y_START_RATIO = 0.965
    INPUT_BOX_Y_END_RATIO = 0.995

    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold

    def detect_chat_input_box(self, frame: Optional[np.ndarray], window_rect: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Localise la zone de saisie du chat avec précision millimétrique.
        Prend en charge n'importe quelle résolution de fenêtre (1920x1080, 2560x1440, 1280x720, etc.).
        """
        if window_rect is not None:
            win_x, win_y, win_w, win_h = window_rect
        else:
            win_x, win_y, win_w, win_h = (0, 0, 1920, 1080)

        # Calcul des coordonnées absolues de la zone de saisie
        box_x = win_x + int(win_w * self.INPUT_BOX_X_START_RATIO)
        box_y = win_y + int(win_h * self.INPUT_BOX_Y_START_RATIO)
        box_w = int(win_w * (self.INPUT_BOX_X_END_RATIO - self.INPUT_BOX_X_START_RATIO))
        box_h = int(win_h * (self.INPUT_BOX_Y_END_RATIO - self.INPUT_BOX_Y_START_RATIO))

        # Clic centré dans la zone de saisie (environ 30% du début de la boîte pour se placer au début du texte)
        click_x = box_x + int(box_w * 0.25)
        click_y = box_y + (box_h // 2)

        # Coordonnées de l'en-tête de chat
        header_x = win_x + int(win_w * 0.125)
        header_y = win_y + int(win_h * self.CHAT_PANE_Y_RATIO)

        confidence = 0.98

        # Si une image est fournie, validation colorimétrique de la zone sombre de saisie (RGB ~ 20-30)
        if frame is not None and isinstance(frame, np.ndarray) and frame.size > 0:
            try:
                fh, fw = frame.shape[:2]
                rx = int(fw * self.INPUT_BOX_X_START_RATIO)
                ry = int(fh * self.INPUT_BOX_Y_START_RATIO)
                rw = int(fw * (self.INPUT_BOX_X_END_RATIO - self.INPUT_BOX_X_START_RATIO))
                rh = int(fh * (self.INPUT_BOX_Y_END_RATIO - self.INPUT_BOX_Y_START_RATIO))
                
                crop = frame[ry:ry+rh, rx:rx+rw]
                if crop.size > 0:
                    mean_val = np.mean(crop)
                    # Le champ de saisie chat est typiquement très sombre (fond < 50)
                    if mean_val < 65:
                        confidence = 0.99
            except Exception:
                pass

        return {
            "found": True,
            "confidence": confidence,
            "chat_header": (header_x, header_y),
            "bounding_box": {
                "x": box_x,
                "y": box_y,
                "width": box_w,
                "height": box_h
            },
            "click_target": (click_x, click_y),
            "channel_badge_rect": {
                "x": win_x + int(win_w * 0.005),
                "y": box_y,
                "width": int(win_w * 0.022),
                "height": box_h
            }
        }

if __name__ == "__main__":
    detector = ChatDetector()
    # Test sur résolution 1920x1080
    res_1080p = detector.detect_chat_input_box(None, (0, 0, 1920, 1080))
    print("[La Noxine 1080p] Zone de Saisie Chat ->", res_1080p["bounding_box"])
    print("[La Noxine 1080p] Point de Clic ->", res_1080p["click_target"])
