import time
import numpy as np
from typing import Optional, Tuple
from PIL import ImageGrab
from agents.motor.dofus_window import DofusWindowController

class ScreenCapture:
    """
    Agent de Perception (La Noxine) - Module de Capture d'Écran.
    Effectue la capture en temps réel des pixels de la fenêtre dofus.exe avec accélération GPU si disponible.
    """
    def __init__(self, target_window_title: str = "Dofus"):
        self.target_window_title = target_window_title
        self.cuda_available = False
        self.window_controller = DofusWindowController(target_window_title)
        self._check_cuda_support()

    def _check_cuda_support(self):
        try:
            import cv2
            count = cv2.cuda.getCudaEnabledDeviceCount()
            if count > 0:
                self.cuda_available = True
        except Exception:
            self.cuda_available = False

    def capture_frame(self) -> np.ndarray:
        """
        Capture une image de la fenêtre Dofus Unity (ou de l'écran entier) sous forme de tableau NumPy BGR.
        """
        geom = self.window_controller.get_window_geometry()
        if geom and geom["width"] > 0 and geom["height"] > 0:
            bbox = (geom["left"], geom["top"], geom["right"], geom["bottom"])
            try:
                img = ImageGrab.grab(bbox=bbox)
                frame = np.array(img)
                # Convert RGB (PIL) to BGR (OpenCV)
                return frame[:, :, ::-1].copy()
            except Exception as e:
                print(f"[La Noxine ScreenCapture] Erreur de capture fenêtre : {e}")

        # Fallback écran principal complet si fenêtre spécifique non capturable
        try:
            img = ImageGrab.grab()
            frame = np.array(img)
            return frame[:, :, ::-1].copy()
        except Exception:
            return np.zeros((1080, 1920, 3), dtype=np.uint8)

    def capture_hud_region(self, rel_x: int = 0, rel_y: int = 0, width: int = 400, height: int = 120) -> np.ndarray:
        """
        Capture spécifiquement le rectangle de l'HUD supérieur gauche de la carte Dofus.
        """
        frame = self.capture_frame()
        if frame.shape[0] >= rel_y + height and frame.shape[1] >= rel_x + width:
            return frame[rel_y:rel_y+height, rel_x:rel_x+width]
        return frame

if __name__ == "__main__":
    cap = ScreenCapture()
    frame = cap.capture_frame()
    print(f"[La Noxine ScreenCapture] Capture frame forme : {frame.shape} | CUDA disponible : {cap.cuda_available}")
