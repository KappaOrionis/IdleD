import numpy as np
from typing import Dict, Any, List, Optional
from agents.vision.base_detector import BaseObjectDetector
from agents.vision.sun_node_detector import SunNodeDetector
from agents.vision.ore_detector import OreDetector

class VisionObjectRegistry:
    """
    Registre & Pipeline Central d'Analyse Visuelle d'Objets (La Noxine).
    
    Permet d'enregistrer, d'activer et d'exécuter dynamiquement n'importe quel détecteur d'objet
    du jeu (Plots de soleil, Zaaps, Minerais, Monstres, PNJs, Coffres, etc.).
    """
    def __init__(self):
        self._detectors: Dict[str, BaseObjectDetector] = {}
        self._register_default_detectors()

    def _register_default_detectors(self):
        """
        Enregistre les détecteurs natifs au démarrage.
        """
        self.register_detector(SunNodeDetector())
        self.register_detector(OreDetector())

    def register_detector(self, detector: BaseObjectDetector):
        """
        Enregistre un nouveau détecteur d'objet dans la pipeline.
        """
        self._detectors[detector.name] = detector
        print(f"[La Noxine Registry] Détecteur d'objet '{detector.name}' enregistré.")

    def unregister_detector(self, name: str):
        """
        Retire un détecteur d'objet de la pipeline.
        """
        if name in self._detectors:
            del self._detectors[name]
            print(f"[La Noxine Registry] Détecteur '{name}' désenregistré.")

    def get_detector(self, name: str) -> Optional[BaseObjectDetector]:
        return self._detectors.get(name)

    def analyze_all_objects(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Exécute la détection pour l'ensemble des objets enregistrés sur l'image courante.
        Retourne un dictionnaire agrégeant tous les objets repérés :
        {
            "sun_node": {"count": 2, "found": True, "detections": [...]},
            "zaap": {"count": 0, "found": False, "detections": []},
            ...
        }
        """
        results = {}
        for name, detector in self._detectors.items():
            try:
                results[name] = detector.detect(frame)
            except Exception as e:
                print(f"[La Noxine Registry] Erreur détection '{name}': {e}")
                results[name] = {"object_type": name, "count": 0, "found": False, "detections": [], "error": str(e)}
        return results

if __name__ == "__main__":
    registry = VisionObjectRegistry()
    dummy_frame = np.zeros((400, 400, 3), dtype=np.uint8)
    res = registry.analyze_all_objects(dummy_frame)
    print(f"[La Noxine Registry] Analyse globale -> {res}")
