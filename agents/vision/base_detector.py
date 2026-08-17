from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, List, Optional

class BaseObjectDetector(ABC):
    """
    Classe de base abstraite pour tous les détecteurs visuels d'objets (La Noxine).
    Chaque nouveau type d'objet du jeu (ex: SunNode, Zaap, Minerai, Monstre, etc.)
    héritera de cette classe pour garantir un contrat d'interface propre et extensible.
    """
    def __init__(self, name: str, confidence_threshold: float = 0.50):
        self.name = name
        self.confidence_threshold = confidence_threshold

    @abstractmethod
    def detect(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Analyse l'image (frame BGR) et retourne un dictionnaire standardisé :
        {
            "object_type": str,
            "count": int,
            "detections": [{'x': int, 'y': int, 'w': int, 'h': int, 'confidence': float, ...}],
            "found": bool
        }
        """
        pass
