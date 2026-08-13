import math
import random
import time
from typing import List, Tuple

class BezierMouse:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Mouvements de Souris Humanisés.
    Génère des courbes de Bézier cubiques non linéaires avec variations de vitesse et dispersion.
    """
    def __init__(self, speed_factor: float = 1.0):
        self.speed_factor = speed_factor

    def _bezier_point(self, p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], t: float) -> Tuple[int, int]:
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        return (int(x), int(y))

    def generate_trajectory(self, start: Tuple[int, int], end: Tuple[int, int], steps: int = 25) -> List[Tuple[int, int]]:
        """
        Génère une trajectoire de points le long d'une courbe de Bézier réaliste.
        """
        # Points de contrôle intermédiaires avec déviation aléatoire (poignet humain)
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
            # Variation non-linéaire du temps (accélération puis décélération)
            t_smooth = t * t * (3 - 2 * t)
            pt = self._bezier_point(p0, p1, p2, p3, t_smooth)
            trajectory.append(pt)

        return trajectory

    def move_and_click(self, start: Tuple[int, int], target: Tuple[int, int], click_radius: int = 5):
        """
        Déplace la souris le long de la courbe et effectue un clic avec rayon d'incertitude aléatoire.
        """
        target_x = target[0] + random.randint(-click_radius, click_radius)
        target_y = target[1] + random.randint(-click_radius, click_radius)

        points = self.generate_trajectory(start, (target_x, target_y))
        
        # Simulation d'exécution mécanique
        for p in points:
            # os_mouse_move(p[0], p[1])
            time.sleep(random.uniform(0.005, 0.015) / self.speed_factor)

        # Pause pré-clic humanisée
        time.sleep(random.uniform(0.05, 0.15))
        # os_mouse_click()
        return (target_x, target_y)

if __name__ == "__main__":
    mouse = BezierMouse()
    path = mouse.generate_trajectory((100, 100), (500, 400))
    print(f"[Le Scaphandre] Trajectoire de Bézier générée avec {len(path)} points.")
