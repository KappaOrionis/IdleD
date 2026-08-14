import time
import ctypes
import numpy as np
from typing import Optional, Tuple, Dict, Any
from PIL import ImageGrab
from agents.motor.dofus_window import DofusWindowController

class ScreenCapture:
    """
    Agent de Perception (La Noxine) - Module de Capture d'Écran DXGI & Windows Win32.
    Utilise le sous-système DirectX Graphics Infrastructure (DXGI / Desktop Duplication API)
    pour récupérer les frames et l'état visuel du jeu Dofus Unity en très haute vitesse et faible latence.
    """
    def __init__(self, target_window_title: str = "Dofus"):
        self.target_window_title = target_window_title
        self.cuda_available = False
        self.dxgi_enabled = False
        self.window_controller = DofusWindowController(target_window_title)
        self._dxcam_instance = None
        
        self._check_cuda_support()
        self._init_dxgi_engine()

    def _check_cuda_support(self):
        try:
            import cv2
            count = cv2.cuda.getCudaEnabledDeviceCount()
            if count > 0:
                self.cuda_available = True
        except Exception:
            self.cuda_available = False

    def _init_dxgi_engine(self):
        """
        Initialise le moteur DXGI Desktop Duplication API via dxcam / win32 si disponible.
        """
        try:
            import dxcam
            self._dxcam_instance = dxcam.create(output_color="BGR")
            if self._dxcam_instance:
                self.dxgi_enabled = True
                print("[La Noxine ScreenCapture] Moteur DXGI Desktop Duplication API initialisé avec succès.")
        except Exception:
            self.dxgi_enabled = False
            print("[La Noxine ScreenCapture] DXGI natif indisponible, utilisation du sous-système Win32/GDI High-Speed.")

    def capture_frame(self) -> np.ndarray:
        """
        Capture une image de la fenêtre Dofus Unity (ou de l'écran) sous forme de tableau NumPy BGR via DXGI ou GDI.
        """
        geom = self.window_controller.get_window_geometry()

        # Stratégie 1 : DXGI Desktop Duplication si activé
        if self.dxgi_enabled and self._dxcam_instance:
            try:
                frame = self._dxcam_instance.grab()
                if frame is not None:
                    if geom and geom["width"] > 0 and geom["height"] > 0:
                        top = max(0, geom["top"])
                        left = max(0, geom["left"])
                        bottom = min(frame.shape[0], geom["bottom"])
                        right = min(frame.shape[1], geom["right"])
                        if bottom > top and right > left:
                            return frame[top:bottom, left:right]
                    return frame
            except Exception as e:
                print(f"[La Noxine DXGI] Erreur de capture DXGI : {e}")

        # Stratégie 2 : Win32 / PIL GDI Fallback
        if geom and geom["width"] > 0 and geom["height"] > 0:
            bbox = (geom["left"], geom["top"], geom["right"], geom["bottom"])
            try:
                img = ImageGrab.grab(bbox=bbox)
                frame = np.array(img)
                # Convert RGB (PIL) to BGR (OpenCV)
                return frame[:, :, ::-1].copy()
            except Exception as e:
                print(f"[La Noxine ScreenCapture] Erreur de capture GDI fenêtre : {e}")

        # Fallback écran principal complet si fenêtre spécifique non capturable
        try:
            img = ImageGrab.grab()
            frame = np.array(img)
            return frame[:, :, ::-1].copy()
        except Exception:
            return np.zeros((1080, 1920, 3), dtype=np.uint8)

    def capture_hud_region(self, rel_x: int = 0, rel_y: int = 0, width: int = 400, height: int = 120) -> np.ndarray:
        """
        Capture spécifiquement le rectangle de l'HUD supérieur gauche de la carte Dofus via DXGI/GDI.
        """
        frame = self.capture_frame()
        if frame.shape[0] >= rel_y + height and frame.shape[1] >= rel_x + width:
            return frame[rel_y:rel_y+height, rel_x:rel_x+width]
        return frame

if __name__ == "__main__":
    cap = ScreenCapture()
    frame = cap.capture_frame()
    print(f"[La Noxine ScreenCapture] Capture frame forme : {frame.shape} | DXGI Actif : {cap.dxgi_enabled} | CUDA : {cap.cuda_available}")

