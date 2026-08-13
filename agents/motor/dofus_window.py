import ctypes
import time
from typing import Optional, Tuple, Dict, Any

# Titre par défaut et nom d'exécutable pour Dofus Unity
TARGET_WINDOW_TITLE = "Dofus"
TARGET_PROCESS_NAME = "dofus.exe"

class DofusWindowController:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Module d'Interaction Fenêtre Windows (dofus.exe).
    Utilise l'API Win32 native (ctypes) sans dépendances lourdes externes pour:
    - Détecter le Handle (HWND) du client Dofus Unity
    - Obtenir la géométrie exacte de la fenêtre (rect & client area)
    - Activer / Mettre au premier plan la fenêtre dofus.exe
    - Convertir les coordonnées relatives du jeu en coordonnées absolues écran
    """
    def __init__(self, window_title: str = TARGET_WINDOW_TITLE):
        self.window_title = window_title
        self.user32 = ctypes.windll.user32
        self.hwnd = None

    def find_window(self) -> Optional[int]:
        """
        Recherche le handle HWND de la fenêtre Dofus.
        """
        hwnd = self.user32.FindWindowW(None, self.window_title)
        if hwnd != 0:
            self.hwnd = hwnd
            return hwnd
        
        # Fallback enum windows si le titre contient Dofus
        found_hwnd = []

        def enum_windows_callback(h, extra):
            length = self.user32.GetWindowTextLengthW(h)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(h, buffer, length + 1)
                if "dofus" in buffer.value.lower():
                    found_hwnd.append(h)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        self.user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        if found_hwnd:
            self.hwnd = found_hwnd[0]
            return self.hwnd
        return None

    def focus_window(self) -> bool:
        """
        Restaure et place la fenêtre dofus.exe au premier plan.
        """
        if not self.hwnd:
            self.find_window()

        if self.hwnd:
            # ShowWindow SW_RESTORE (9)
            self.user32.ShowWindow(self.hwnd, 9)
            # SetForegroundWindow
            self.user32.SetForegroundWindow(self.hwnd)
            time.sleep(0.1)
            return True
        return False

    def get_window_geometry(self) -> Optional[Dict[str, int]]:
        """
        Retourne la position et les dimensions de la fenêtre (left, top, right, bottom, width, height).
        """
        if not self.hwnd:
            self.find_window()

        if not self.hwnd:
            return None

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long)]

        rect = RECT()
        if self.user32.GetWindowRect(self.hwnd, ctypes.byref(rect)):
            return {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top
            }
        return None

    def client_to_screen(self, rel_x: int, rel_y: int) -> Optional[Tuple[int, int]]:
        """
        Convertit une coordonnée relative à la fenêtre Dofus Unity en coordonnée écran absolue.
        """
        geom = self.get_window_geometry()
        if not geom:
            return None
        return (geom["left"] + rel_x, geom["top"] + rel_y)

if __name__ == "__main__":
    controller = DofusWindowController()
    hwnd = controller.find_window()
    print(f"[Le Scaphandre] Détection fenêtre Dofus HWND: {hwnd}")
    if hwnd:
        geom = controller.get_window_geometry()
        print(f"[Le Scaphandre] Géométrie fenêtre: {geom}")
