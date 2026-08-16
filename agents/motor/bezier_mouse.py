import ctypes
from ctypes import wintypes
import math
import random
import time
from typing import List, Tuple, Optional
from agents.motor.active_window import ActiveWindowController
from agents.motor.pid_sim import PIDMouseTrajectory, PIDDeviceIdentity

# DirectInput / Win32 Mouse Flags (Périphérique matériel réel)
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]

class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ii", Input_I)
    ]

INPUT_MOUSE = 0

class BezierMouse:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Mouvements de Souris Humanisés & Clics Périphériques Réels (SendInput).
    Génère des mouvements et clics physiques au niveau matériel OS :
    - Trajectoires dynamiques contrôlées par régulateurs PID (Proportionnel - Intégral - Dérivé)
    - Simulation d'identité périphérique USB PID/VID (Logitech G Pro)
    - Injection physique SendInput Win32 simulant un capteur optique réel
    - Clics avec temps de maintien (Hold Time) gaussien.
    """
    def __init__(self, speed_factor: float = 1.0):
        self.speed_factor = max(0.1, speed_factor)
        self.user32 = ctypes.windll.user32
        self.active_window = ActiveWindowController()
        self.pid_trajectory = PIDMouseTrajectory()
        self.device_identity = PIDDeviceIdentity()

    def get_current_cursor_pos(self) -> Tuple[int, int]:
        """Obtient la position courante du curseur à l'écran."""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _send_mouse_input(self, flags: int, dx: int = 0, dy: int = 0, data: int = 0):
        """Envoie un événement souris physique via SendInput OS."""
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(dx, dy, data, flags, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(INPUT_MOUSE), ii_)
        self.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def _bezier_point(self, p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], t: float) -> Tuple[int, int]:
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        return (int(round(x)), int(round(y)))

    def generate_trajectory(self, start: Tuple[int, int], end: Tuple[int, int], steps: Optional[int] = None) -> List[Tuple[int, int]]:
        """Génère une trajectoire de Bézier réaliste."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.hypot(dx, dy)

        if steps is None:
            steps = max(15, int(distance / 20))

        dev_scale = min(60.0, distance * 0.25)
        offset_x1 = random.gauss(0, dev_scale)
        offset_y1 = random.gauss(0, dev_scale)
        offset_x2 = random.gauss(0, dev_scale)
        offset_y2 = random.gauss(0, dev_scale)

        p0 = start
        p1 = (int(start[0] + dx * 0.33 + offset_x1), int(start[1] + dy * 0.33 + offset_y1))
        p2 = (int(start[0] + dx * 0.66 + offset_x2), int(start[1] + dy * 0.66 + offset_y2))
        p3 = end

        trajectory = []
        for i in range(steps + 1):
            t = i / steps
            t_smooth = t * t * (3.0 - 2.0 * t)
            pt = self._bezier_point(p0, p1, p2, p3, t_smooth)
            trajectory.append(pt)

        if distance > 150 and random.random() < 0.15:
            overshoot_x = int(end[0] + random.gauss(0, 3))
            overshoot_y = int(end[1] + random.gauss(0, 3))
            trajectory.append((overshoot_x, overshoot_y))
            trajectory.append(end)

        return trajectory

    def move_cursor_to(self, target_x: int, target_y: int, start_pos: Optional[Tuple[int, int]] = None):
        """
        Déplace physiquement le curseur vers les coordonnées cibles via régulateurs PID.
        """
        start = start_pos if start_pos else self.get_current_cursor_pos()
        points = self.pid_trajectory.generate_points(start, (target_x, target_y))

        for p in points:
            self.user32.SetCursorPos(p[0], p[1])
            step_delay = max(0.004, random.gauss(0.010, 0.002)) / self.speed_factor
            time.sleep(step_delay)

    def click(self, button: str = "left", hold_mean_sec: float = 0.065):
        """Émet un clic matériel physique SendInput."""
        down_flag = MOUSEEVENTF_LEFTDOWN if button == "left" else MOUSEEVENTF_RIGHTDOWN
        up_flag = MOUSEEVENTF_LEFTUP if button == "left" else MOUSEEVENTF_RIGHTUP

        self._send_mouse_input(down_flag)
        hold_time = max(0.025, random.gauss(hold_mean_sec, 0.015)) / self.speed_factor
        time.sleep(hold_time)
        self._send_mouse_input(up_flag)

    def click_in_active_window(self, rel_x: int, rel_y: int, button: str = "left", click_radius: int = 3) -> Optional[Tuple[int, int]]:
        """
        Convertit la coordonnée relative à la fenêtre active en coordonnée écran, déplace la souris et clique.
        """
        abs_coords = self.active_window.client_to_screen(rel_x, rel_y)
        if not abs_coords:
            abs_coords = (rel_x, rel_y)

        target_x = int(abs_coords[0] + random.gauss(0, max(1, click_radius / 2.0)))
        target_y = int(abs_coords[1] + random.gauss(0, max(1, click_radius / 2.0)))

        self.move_cursor_to(target_x, target_y)
        time.sleep(random.uniform(0.04, 0.1))
    def swipe_opposite_direction(self, direction_key: str, distance_px: int = 150):
        """
        Effectue un glisser-déposer (Swipe) fluide de la souris dans la direction opposée :
        - Touche 'Up' (Haut) -> Swipe vers le Bas (Down)
        - Touche 'Down' (Bas) -> Swipe vers le Haut (Up)
        - Touche 'Left' (Gauche) -> Swipe vers la Droite (Right)
        - Touche 'Right' (Droite) -> Swipe vers la Gauche (Left)
        Permet au personnage de changer de carte / écran de jeu instantanément.
        """
        rect = self.active_window.get_active_window_rect()
        if rect:
            win_x, win_y, win_w, win_h = rect
            center_x = win_x + (win_w // 2)
            center_y = win_y + (win_h // 2)
        else:
            center_x, center_y = self.get_current_cursor_pos()

        dir_lower = direction_key.lower()

        # Le swipe démarre au centre exact de l'écran et s'étend dans la direction opposée
        start_x, start_y = center_x, center_y

        if dir_lower in ["up", "haut"]:
            # Touche Haut (↑) -> Swipe depuis le centre vers le bas
            end_x, end_y = center_x, center_y + distance_px
        elif dir_lower in ["down", "bas"]:
            # Touche Bas (↓) -> Swipe depuis le centre vers le haut
            end_x, end_y = center_x, center_y - distance_px
        elif dir_lower in ["left", "gauche"]:
            # Touche Gauche (←) -> Swipe depuis le centre vers la droite
            end_x, end_y = center_x + distance_px, center_y
        else: # Right / Droite
            # Touche Droite (→) -> Swipe depuis le centre vers la gauche
            end_x, end_y = center_x - distance_px, center_y

        print(f"[Le Scaphandre] Swipe centré maintenu ({direction_key} -> départ centre: {start_x},{start_y} vers {end_x},{end_y})")

        # 1. Positionnement initial au centre de l'écran
        self.move_cursor_to(start_x, start_y)
        time.sleep(0.04)

        # 2. Pression du bouton gauche (maintenu enfoncé)
        self._send_mouse_input(MOUSEEVENTF_LEFTDOWN)
        time.sleep(0.05)

        # 3. Glissement interpolé fluide avec clic maintenu
        steps = 14
        for i in range(1, steps + 1):
            t = i / float(steps)
            smooth_t = 1.0 - (1.0 - t) ** 2
            inter_x = int(start_x + (end_x - start_x) * smooth_t)
            inter_y = int(start_y + (end_y - start_y) * smooth_t)
            self.user32.SetCursorPos(inter_x, inter_y)
            time.sleep(0.01)

        # 4. Relâchement du bouton gauche à destination
        time.sleep(0.05)
        self._send_mouse_input(MOUSEEVENTF_LEFTUP)
        time.sleep(0.03)

if __name__ == "__main__":
    mouse = BezierMouse()
    print("Curseur actuel :", mouse.get_current_cursor_pos())
