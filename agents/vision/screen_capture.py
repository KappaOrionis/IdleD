import time
import numpy as np
from typing import Optional, Dict
from PIL import ImageGrab
from agents.motor.active_window import ActiveWindowController

class ScreenCapture:
    """
    Agent de Perception (La Noxine) - Module de Capture d'Écran Générique.
    Capture les frames de la fenêtre active au premier plan (ou de l'écran) en haute vitesse.
    """
    def __init__(self):
        self.cuda_available = False
        self.dxgi_enabled = False
        self.window_controller = ActiveWindowController()
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
        try:
            import dxcam
            self._dxcam_instance = dxcam.create(output_color="BGR")
            if self._dxcam_instance:
                self.dxgi_enabled = True
        except Exception:
            self.dxgi_enabled = False

    def capture_frame(self) -> np.ndarray:
        """
        Capture une image de la fenêtre active sous forme de tableau NumPy BGR.
        """
        geom = self.window_controller.get_active_window_geometry()

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
            except Exception:
                pass

        # Stratégie 2 : Win32 / PIL GDI Fallback
        if geom and geom["width"] > 0 and geom["height"] > 0:
            bbox = (geom["left"], geom["top"], geom["right"], geom["bottom"])
            try:
                img = ImageGrab.grab(bbox=bbox)
                frame = np.array(img)
                return frame[:, :, ::-1].copy()
            except Exception:
                pass

        # Fallback plein écran
        try:
            img = ImageGrab.grab()
            frame = np.array(img)
            return frame[:, :, ::-1].copy()
        except Exception:
            return np.zeros((720, 1280, 3), dtype=np.uint8)

if __name__ == "__main__":
    cap = ScreenCapture()
    frame = cap.capture_frame()
    print("ScreenCapture shape:", frame.shape)
