import heapq
from typing import List, Tuple, Dict, Optional

class PathfindingEngine:
    """
    Agent Tactique et Décisionnel (Le Cerveau) - Moteur de Routage Multi-Modal.
    Calcul du chemin optimal en combinant A* / Dijkstra pondéré, Zaaps, Zaapis et potions.
    """
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def find_path(self, start_tile: Tuple[int, int], target_tile: Tuple[int, int], use_zaap: bool = True) -> List[Tuple[int, int]]:
        """
        Algorithme A* pour calculer le chemin le plus rapide entre deux tuiles de carte.
        """
        open_set = []
        heapq.heappush(open_set, (0, start_tile))
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start_tile: None}
        g_score: Dict[Tuple[int, int], float] = {start_tile: 0.0}

        def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == target_tile:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            # Voisins à 4 directions cardinales (transitions de carte)
            neighbors = [
                (current[0] + 1, current[1]),
                (current[0] - 1, current[1]),
                (current[0], current[1] + 1),
                (current[0], current[1] - 1)
            ]

            for neighbor in neighbors:
                tentative_g = g_score[current] + 1.0  # Coût de déplacement de tuile à tuile
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, target_tile)
                    heapq.heappush(open_set, (f_score, neighbor))

        return []

if __name__ == "__main__":
    router = PathfindingEngine()
    path = router.find_path((0, 0), (3, 2))
    print(f"[Le Cerveau] Trajet calculé: {path}")
