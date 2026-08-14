import ctypes
import time
from typing import Optional, Tuple, Dict, Any, List

TARGET_PROCESS_NAMES = ["dofus.exe", "dofus3.exe", "dofus-unity.exe", "dofus"]
TARGET_TITLE_KEYWORDS = ["dofus", "amakna", "sufokia", "astrub"]

class DofusWindowController:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Module d'Interaction Fenêtre Windows (dofus.exe).
    Utilise l'API Win32 native (ctypes) sans dépendances lourdes externes pour:
    - Détecter le Handle (HWND) du client Dofus Unity via Titre ou Processus
    - Obtenir la géométrie exacte de la fenêtre et de la zone cliente de jeu (client rect)
    - Activer / Mettre au premier plan la fenêtre dofus.exe
    - Convertir les coordonnées relatives du jeu en coordonnées absolues écran
    """
    def __init__(self, window_title_keyword: str = "dofus"):
        self.window_title_keyword = window_title_keyword.lower()
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.hwnd = None
        self._init_dpi_awareness()

    def _init_dpi_awareness(self):
        """Active la prise en charge DPI per-monitor sous Windows pour éviter les décalages de coordonnées."""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                self.user32.SetProcessDPIAware()
            except Exception:
                pass

    def find_window(self) -> Optional[int]:
        """
        Recherche le handle HWND de la fenêtre Dofus Unity via EnumDesktopWindows et détection par PID / Titre.
        """
        found_hwnds: List[Tuple[int, str, int]] = []
        user32 = self.user32
        h_desk = user32.OpenInputDesktop(0, False, 0x01FF) or user32.GetThreadDesktop(self.kernel32.GetCurrentThreadId())

        def enum_desktop_callback(h, extra):
            # Obtenir le PID associé au HWND
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
            
            # Obtenir le Titre de la fenêtre
            length = user32.GetWindowTextLengthW(h)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(h, buffer, length + 1)
                title = buffer.value
                title_lower = title.lower()

                # Critères Dofus Unity : mot-clé titre ou signature Release de Dofus Unity (ex: "Kometes - ... - Release")
                if any(kw in title_lower for kw in TARGET_TITLE_KEYWORDS) or "release" in title_lower or "unity" in title_lower:
                    found_hwnds.append((h, title, pid.value))
            return True

        if h_desk:
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumDesktopWindows(h_desk, WNDENUMPROC(enum_desktop_callback), 0)

        if found_hwnds:
            self.hwnd = found_hwnds[0][0]
            print(f"[Dofus Window] Fenêtre Dofus détectée : '{found_hwnds[0][1]}' (HWND: {self.hwnd}, PID: {found_hwnds[0][2]})")
            return self.hwnd

        print("[Dofus Window] Aucune fenêtre de jeu Dofus active trouvée sur le bureau.")
        self.hwnd = None
        return None

    def is_game_running(self) -> bool:
        """
        Vérifie si le client de jeu Dofus Unity est actuellement détecté.
        """
        return self.find_window() is not None

    def focus_window(self) -> bool:
        """
        Restaure et place la fenêtre dofus.exe au premier plan de façon garantie sous Windows Win32.
        """
        if not self.hwnd:
            self.find_window()

        if self.hwnd:
            # 1. Utiliser SwitchToThisWindow (API Win32 dédiée au switch direct)
            try:
                self.user32.SwitchToThisWindow(self.hwnd, True)
            except Exception:
                pass

            # 2. Restauration si réduite
            if self.user32.IsIconic(self.hwnd):
                self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE

            self.user32.ShowWindow(self.hwnd, 5)  # SW_SHOW
            self.user32.SetForegroundWindow(self.hwnd)
            self.user32.BringWindowToTop(self.hwnd)

            time.sleep(0.05)
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

    def get_client_geometry(self) -> Optional[Dict[str, int]]:
        """
        Retourne la géométrie exacte de l'espace de rendu intérieur du jeu (hors barre de titre et bordures).
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

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        client_rect = RECT()
        if self.user32.GetClientRect(self.hwnd, ctypes.byref(client_rect)):
            pt = POINT(0, 0)
            self.user32.ClientToScreen(self.hwnd, ctypes.byref(pt))
            return {
                "left": pt.x,
                "top": pt.y,
                "width": client_rect.right - client_rect.left,
                "height": client_rect.bottom - client_rect.top,
                "right": pt.x + (client_rect.right - client_rect.left),
                "bottom": pt.y + (client_rect.bottom - client_rect.top)
            }
        return self.get_window_geometry()

    def client_to_screen(self, rel_x: int, rel_y: int) -> Optional[Tuple[int, int]]:
        """
        Convertit une coordonnée relative à la zone cliente Dofus Unity en coordonnée écran absolue.
        """
        geom = self.get_client_geometry()
        if not geom:
            return None
        return (geom["left"] + rel_x, geom["top"] + rel_y)

if __name__ == "__main__":
    controller = DofusWindowController()
    hwnd = controller.find_window()
    print(f"[Le Scaphandre] Statut détection Dofus HWND: {hwnd} | En cours: {controller.is_game_running()}")

