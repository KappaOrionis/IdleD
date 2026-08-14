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
    - Obtenir la géométrie exacte de la fenêtre (rect & client area)
    - Activer / Mettre au premier plan la fenêtre dofus.exe
    - Convertir les coordonnées relatives du jeu en coordonnées absolues écran
    """
    def __init__(self, window_title_keyword: str = "dofus"):
        self.window_title_keyword = window_title_keyword.lower()
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.hwnd = None

    def find_window(self) -> Optional[int]:
        """
        Recherche le handle HWND de la fenêtre Dofus via plusieurs stratégies Win32.
        """
        found_hwnds: List[Tuple[int, str]] = []

        def enum_windows_callback(h, extra):
            # Détecter la fenêtre même si elle est minimisée dans la barre des tâches
            length = self.user32.GetWindowTextLengthW(h)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(h, buffer, length + 1)
                title = buffer.value.lower()
                if any(kw in title for kw in TARGET_TITLE_KEYWORDS):
                    # Accepter si la fenêtre est soit visible, soit minimisée (IsIconic)
                    if self.user32.IsWindowVisible(h) or self.user32.IsIconic(h):
                        found_hwnds.append((h, buffer.value))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        self.user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        if found_hwnds:
            # Préférer la première fenêtre visible trouvée
            self.hwnd = found_hwnds[0][0]
            print(f"[Le Scaphandre] Fenêtre Dofus trouvée via titre : '{found_hwnds[0][1]}' (HWND: {self.hwnd})")
            return self.hwnd

        self.hwnd = None
        return None

    def is_game_running(self) -> bool:
        """
        Vérifie si le client de jeu Dofus Unity est actuellement détecté.
        """
        return self.find_window() is not None

    def focus_window(self) -> bool:
        """
        Restaure et place la fenêtre dofus.exe au premier plan même si elle est réduite/minimisée dans la barre des tâches.
        Garantit que la fenêtre est ciblée avant toute commande motrice.
        """
        if not self.hwnd:
            self.find_window()

        if self.hwnd:
            # 1. Vérifier si la fenêtre est réduite/minimisée (IsIconic)
            if self.user32.IsIconic(self.hwnd):
                self.user32.OpenIcon(self.hwnd)  # Restaure une fenêtre minimisée
                self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE = 9

            # 2. Assurer la visibilité et l'activation au premier plan (SW_SHOW = 5)
            self.user32.ShowWindow(self.hwnd, 5)

            # 3. Contourner les restrictions de focus de Windows via AttachThreadInput si besoin
            fore_thread = self.user32.GetWindowThreadProcessId(self.user32.GetForegroundWindow(), None)
            app_thread = self.kernel32.GetCurrentThreadId()

            if fore_thread != app_thread:
                self.user32.AttachThreadInput(fore_thread, app_thread, True)
                self.user32.SetForegroundWindow(self.hwnd)
                self.user32.BringWindowToTop(self.hwnd)
                self.user32.AttachThreadInput(fore_thread, app_thread, False)
            else:
                self.user32.SetForegroundWindow(self.hwnd)

            time.sleep(0.08)
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
    print(f"[Le Scaphandre] Statut détection Dofus HWND: {hwnd} | En cours: {controller.is_game_running()}")
