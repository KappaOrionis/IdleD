import time
import numpy as np
from typing import Optional, Dict
from PIL import ImageGrab
import base64
import io
from agents.motor.active_window import ActiveWindowController

class ActiveWindowCapture:
    """
    Agent de Perception (La Noxine) - Capture d'Écran de la Fenêtre Active & Génération de Vignette.
    Capture en temps réel le contenu de la fenêtre active au premier plan et permet d'exporter
    des vignettes encodées en base64 pour l'interface utilisateur.
    """
    def __init__(self):
        self.window_controller = ActiveWindowController()

    def capture_active_window(self) -> np.ndarray:
        """
        Capture l'image de la fenêtre actuellement active.
        """
        geom = self.window_controller.get_active_window_geometry()
        if geom and geom["width"] > 0 and geom["height"] > 0:
            bbox = (geom["left"], geom["top"], geom["right"], geom["bottom"])
            try:
                img = ImageGrab.grab(bbox=bbox)
                frame = np.array(img)
                return frame[:, :, ::-1].copy() # BGR
            except Exception as e:
                print(f"[ActiveWindowCapture] Erreur capture fenêtre active : {e}")

        # Fallback plein écran
        try:
            img = ImageGrab.grab()
            frame = np.array(img)
            return frame[:, :, ::-1].copy()
        except Exception:
            return np.zeros((300, 400, 3), dtype=np.uint8)

    def get_thumbnail_base64(self, max_width: int = 260, max_height: int = 68) -> Optional[str]:
        """
        Génère une vignette JPEG compressée en base64 zoomée sur le HUD de zone, coordonnées et niveau.
        """
        geom = self.window_controller.get_active_window_geometry()
        if not geom or geom["width"] <= 0 or geom["height"] <= 0:
            return None

        # Zoom sur la région HUD supérieure gauche (30% largeur, 12% hauteur)
        crop_w = int(geom["width"] * 0.30)
        crop_h = int(geom["height"] * 0.12)
        bbox = (
            geom["left"],
            geom["top"],
            geom["left"] + crop_w,
            geom["top"] + crop_h
        )
        try:
            img = ImageGrab.grab(bbox=bbox)
            img.thumbnail((max_width, max_height))
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{img_b64}"
        except Exception as e:
            print(f"[ActiveWindowCapture] Erreur génération vignette zoomée : {e}")
            return None

if __name__ == "__main__":
    cap = ActiveWindowCapture()
    thumb = cap.get_thumbnail_base64()
    print("Vignette base64 générée :", thumb[:60] if thumb else "None")
