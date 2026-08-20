import cv2
import numpy as np
from typing import Dict, Any, Optional
from agents.vision.base_detector import BaseObjectDetector

class OreDetector(BaseObjectDetector):
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur de Gisements de Minerai (Cuivre, Fer, etc.).
    
    Tire parti du mode surbrillance Dofus Unity (Touche 'Y') qui entoure les éléments interactifs
    d'un contour/halo caractéristique, ou détecte directement la texture du gisement de cuivre au sol/paroi.
    """
    def __init__(self, confidence_threshold: float = 0.55):
        super().__init__(name="copper_ore", confidence_threshold=confidence_threshold)
        
        # Plages HSV pour la roche / filon de cuivre (reflets cuivre/orange/marron métallisé)
        self.lower_copper = np.array([5, 80, 70], dtype=np.uint8)
        self.upper_copper = np.array([25, 255, 255], dtype=np.uint8)

        # Plages HSV pour la surbrillance touche 'Y' (Halo lumineux blanc/bleuté/doré)
        self.lower_highlight = np.array([0, 0, 200], dtype=np.uint8)
        self.upper_highlight = np.array([180, 60, 255], dtype=np.uint8)

    def detect(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Détecte les gisements de cuivre interactifs sur la carte.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return {"object_type": self.name, "count": 0, "nodes": [], "detections": [], "found": False}

        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Masque 1 : Couleur naturelle de la roche de cuivre (teinte orangée/cuivrée)
        mask_copper = cv2.inRange(hsv, self.lower_copper, self.upper_copper)
        
        # Masque 2 : Surbrillance (Touche 'Y')
        mask_highlight = cv2.inRange(hsv, self.lower_highlight, self.upper_highlight)

        # Masque combiné
        combined_mask = cv2.bitwise_or(mask_copper, mask_highlight)

        # Exclusion des zones UI (Bandeau haut, Chat bas-gauche, Mini-carte bas-droite)
        combined_mask[0:int(h * 0.05), :] = 0
        combined_mask[int(h * 0.75):, 0:int(w * 0.28)] = 0
        combined_mask[int(h * 0.75):, int(w * 0.70):] = 0
        combined_mask[int(h * 0.85):, :] = 0

        # Nettoyage morphologique
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        cleaned = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_DILATE, kernel, iterations=2)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Surface d'un filon/roche de minerai (typique 100 px² à 6000 px²)
            if 100 <= area <= 6000:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                aspect_ratio = float(bw) / bh if bh > 0 else 0
                
                if 0.4 <= aspect_ratio <= 2.8:
                    confidence = round(min(0.99, 0.55 + (area / 4000.0) * 0.40), 2)
                    detections.append({
                        "x": int(bx + bw // 2),
                        "y": int(by + bh // 2),
                        "w": int(bw),
                        "h": int(bh),
                        "area": float(area),
                        "confidence": confidence
                    })

        # Filtrage des doublons proches
        filtered = []
        for det in detections:
            duplicate = False
            for existing in filtered:
                dist = np.sqrt((det["x"] - existing["x"])**2 + (det["y"] - existing["y"])**2)
                if dist < 45:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(det)

        return {
            "object_type": self.name,
            "count": len(filtered),
            "nodes": filtered,
            "detections": filtered,
            "found": len(filtered) > 0
        }

if __name__ == "__main__":
    detector = OreDetector()
    dummy = np.zeros((400, 400, 3), dtype=np.uint8)
    print("Test OreDetector ->", detector.detect(dummy))
