import ctypes
import math
import random
import time
from typing import List, Tuple, Optional
from agents.motor.dofus_window import DofusWindowController

class BezierMouse:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Mouvements de Souris Humanisés & Clics Physiques.
    Génère des courbes de Bézier cubiques non linéaires avec:
    - Distribution Gaussienne des points de déviation et des délais (Biomecanique)
    - Modélisation de la vitesse (Loi de Fitts & Ease-In-Out)
    - Gestion de l'Overshoot et micro-corrections
    - Temps de maintien de clic réaliste (Click Hold Time)
    - Injection physique Win32 SendInput / mouse_event
    """
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010

    def __init__(self, speed_factor: float = 1.0):
        self.speed_factor = max(0.1, speed_factor)
        self.user32 = ctypes.windll.user32
        self.window_controller = DofusWindowController()

    def get_current_cursor_pos(self) -> Tuple[int, int]:
        """Obtient la position courante du curseur de la souris à l'écran."""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def _bezier_point(self, p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], t: float) -> Tuple[int, int]:
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        return (int(round(x)), int(round(y)))

    def generate_trajectory(self, start: Tuple[int, int], end: Tuple[int, int], steps: Optional[int] = None) -> List[Tuple[int, int]]:
        """
        Génère une trajectoire de points le long d'une courbe de Bézier réaliste
        avec vitesse adaptée selon la distance (Loi de Fitts).
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.hypot(dx, dy)

        # Calcul dynamique du nombre d'étapes basé sur la distance
        if steps is None:
            steps = max(15, int(distance / 20))

        # Déviation Gaussienne des points de contrôle
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
            # Polynôme d'accélération / décélération Ease-in-out
            t_smooth = t * t * (3.0 - 2.0 * t)
            pt = self._bezier_point(p0, p1, p2, p3, t_smooth)
            trajectory.append(pt)

        # Probabilité de micro-dépassement (Overshoot) suivi de correction (15% des cas)
        if distance > 150 and random.random() < 0.15:
            overshoot_x = int(end[0] + random.gauss(0, 3))
            overshoot_y = int(end[1] + random.gauss(0, 3))
            trajectory.append((overshoot_x, overshoot_y))
            trajectory.append(end)

        return trajectory

    def move_cursor_to(self, target_x: int, target_y: int, start_pos: Optional[Tuple[int, int]] = None):
        """
        Déplace physiquement le curseur vers les coordonnées absolues cibles.
        """
        start = start_pos if start_pos else self.get_current_cursor_pos()
        points = self.generate_trajectory(start, (target_x, target_y))

        for p in points:
            self.user32.SetCursorPos(p[0], p[1])
            step_delay = max(0.003, random.gauss(0.008, 0.003)) / self.speed_factor
            time.sleep(step_delay)

    def click(self, button: str = "left", hold_mean_sec: float = 0.065):
        """
        Émet un clic physique avec temps de maintien (Hold Time) distribué selon une Gaussienne.
        """
        down_flag = self.MOUSEEVENTF_LEFTDOWN if button == "left" else self.MOUSEEVENTF_RIGHTDOWN
        up_flag = self.MOUSEEVENTF_LEFTUP if button == "left" else self.MOUSEEVENTF_RIGHTUP

        # Mouse Down
        self.user32.mouse_event(down_flag, 0, 0, 0, 0)

        # Maintien du clic réaliste (~65ms)
        hold_time = max(0.025, random.gauss(hold_mean_sec, 0.015)) / self.speed_factor
        time.sleep(hold_time)

        # Mouse Up
        self.user32.mouse_event(up_flag, 0, 0, 0, 0)

    def move_and_click_target(self, start: Optional[Tuple[int, int]], target_rel: Tuple[int, int], click_radius: int = 4) -> Tuple[int, int]:
        """
        Active la fenêtre dofus.exe, convertit la coordonnée relative du jeu en coordonnée absolue écran,
        déplace le curseur via Bézier et exécute un clic humanisé.
        """
        # Focus préalable de la fenêtre Dofus Unity
        focused = self.window_controller.focus_window()
        if not focused:
            print("[Le Scaphandre] Avertissement: Fenêtre Dofus non ciblée avant exécution.")

        # Conversion en coordonnée écran absolue
        screen_coords = self.window_controller.client_to_screen(target_rel[0], target_rel[1])
        target_abs = screen_coords if screen_coords else target_rel

        # Dispersion gaussienne du clic sur la cible
        target_x = int(target_abs[0] + random.gauss(0, max(1, click_radius / 2.0)))
        target_y = int(target_abs[1] + random.gauss(0, max(1, click_radius / 2.0)))

        actual_start = start if start else self.get_current_cursor_pos()
        self.move_cursor_to(target_x, target_y, start_pos=actual_start)

        # Petite pause pré-clic
        time.sleep(random.uniform(0.04, 0.12))
        self.click("left")

        return (target_x, target_y)

    def execute_action(self, action_func, *args, **kwargs):
        """
        Garantit que la fenêtre Dofus est ciblée/au premier plan avant d'exécuter une action motrice spécifique.
        """
        self.window_controller.focus_window()
        return action_func(*args, **kwargs)

if __name__ == "__main__":
    mouse = BezierMouse()
    path = mouse.generate_trajectory((100, 100), (500, 400))
    print(f"[Le Scaphandre] Trajectoire de Bézier humanisée ({len(path)} points).")
