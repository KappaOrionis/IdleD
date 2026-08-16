import ctypes
from ctypes import wintypes
import time
from typing import Optional, Dict, Tuple

class ActiveWindowController:
    """
    Contrôleur générique de la fenêtre active au premier plan (Foreground / Active Window).
    Permet de récupérer les dimensions, la zone cliente et le titre de n'importe quelle fenêtre active
    sans cibler spécifiquement dofus.exe.
    """
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self._init_dpi_awareness()

    def _init_dpi_awareness(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                self.user32.SetProcessDPIAware()
            except Exception:
                pass

    def get_active_hwnd(self) -> Optional[int]:
        """Retourne le HWND de la fenêtre actuellement au premier plan."""
        hwnd = self.user32.GetForegroundWindow()
        return hwnd if hwnd else None

    def get_active_window_title(self) -> str:
        """Retourne le titre de la fenêtre active courante."""
        hwnd = self.get_active_hwnd()
        if not hwnd:
            return ""
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value
        return ""

    def get_active_window_geometry(self) -> Optional[Dict[str, int]]:
        """Retourne la position et taille de la fenêtre active (left, top, right, bottom, width, height)."""
        hwnd = self.get_active_hwnd()
        if not hwnd:
            return None

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long)]

        rect = RECT()
        if self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top
            }
        return None

    def get_active_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Retourne (x, y, w, h) de la fenêtre active."""
        geom = self.get_active_window_geometry()
        if geom:
            return (geom["left"], geom["top"], geom["width"], geom["height"])
        return None

    def get_active_client_geometry(self) -> Optional[Dict[str, int]]:
        """Retourne la zone cliente de la fenêtre active."""
        hwnd = self.get_active_hwnd()
        if not hwnd:
            return None

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long),
                        ("top", ctypes.c_long),
                        ("right", ctypes.c_long),
                        ("bottom", ctypes.c_long)]

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        client_rect = RECT()
        if self.user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
            pt = POINT(0, 0)
            self.user32.ClientToScreen(hwnd, ctypes.byref(pt))
            return {
                "left": pt.x,
                "top": pt.y,
                "width": client_rect.right - client_rect.left,
                "height": client_rect.bottom - client_rect.top,
                "right": pt.x + (client_rect.right - client_rect.left),
                "bottom": pt.y + (client_rect.bottom - client_rect.top)
            }
        return self.get_active_window_geometry()

    def client_to_screen(self, rel_x: int, rel_y: int) -> Optional[Tuple[int, int]]:
        """Convertit une coordonnée relative à la fenêtre active en coordonnée absolue écran."""
        geom = self.get_active_client_geometry()
        if not geom:
            return None
        return (geom["left"] + rel_x, geom["top"] + rel_y)

if __name__ == "__main__":
    controller = ActiveWindowController()
    print("Active Title:", controller.get_active_window_title())
    print("Active Rect:", controller.get_active_window_geometry())
