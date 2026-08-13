import math
import random
import time
from typing import List, Tuple, Optional
from agents.motor.dofus_window import DofusWindowController

class BezierMouse:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Mouvements de Souris Humanisés.
    Génère des courbes de Bézier cubiques non linéaires avec variations de vitesse et dispersion,
    ciblées sur la fenêtre dofus.exe.
    """
    def __init__(self, speed_factor: float = 1.0):
        self.speed_factor = speed_factor
        self.window_controller = DofusWindowController()

    def _bezier_point(self, p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], t: float) -> Tuple[int, int]:
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        return (int(x), int(y))

    def generate_trajectory(self, start: Tuple[int, int], end: Tuple[int, int], steps: int = 25) -> List[Tuple[int, int]]:
        """
        Génère une trajectoire de points le long d'une courbe de Bézier réaliste.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        control_offset_x = random.randint(-50, 50)
        control_offset_y = random.randint(-50, 50)

        p0 = start
        p1 = (start[0] + dx // 3 + control_offset_x, start[1] + dy // 3 + control_offset_y)
        p2 = (start[0] + 2 * dx // 3 - control_offset_x, start[1] + 2 * dy // 3 - control_offset_y)
        p3 = end

        trajectory = []
        for i in range(steps + 1):
            t = i / steps
            t_smooth = t * t * (3 - 2 * t)
            pt = self._bezier_point(p0, p1, p2, p3, t_smooth)
            trajectory.append(pt)

        return trajectory

    def move_and_click_target(self, start: Tuple[int, int], target_rel: Tuple[int, int], click_radius: int = 5) -> Tuple[int, int]:
        """
        Active la fenêtre dofus.exe, convertit la coordonnée relative de la tuile/cible en coordonnée écran absolue,
        puis déplace la souris le long d'une courbe de Bézier humanisée et clique.
        """
        # Focus de la fenêtre Dofus Unity
        self.window_controller.focus_window()

        # Conversion en coordonnée écran absolue si dofus.exe est ouvert
        screen_coords = self.window_controller.client_to_screen(target_rel[0], target_rel[1])
        target_abs = screen_coords if screen_coords else target_rel

        target_x = target_abs[0] + random.randint(-click_radius, click_radius)
        target_y = target_abs[1] + random.randint(-click_radius, click_radius)

        points = self.generate_trajectory(start, (target_x, target_y))
        
        for p in points:
            time.sleep(random.uniform(0.005, 0.015) / self.speed_factor)

        time.sleep(random.uniform(0.05, 0.15))
        return (target_x, target_y)

if __name__ == "__main__":
    mouse = BezierMouse()
    path = mouse.generate_trajectory((100, 100), (500, 400))
    print(f"[Le Scaphandre] Trajectoire de Bézier ciblée sur dofus.exe générée ({len(path)} points).")
