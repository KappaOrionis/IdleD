import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from agents.vision.base_detector import BaseObjectDetector
from agents.vision.screen_layout import GameScreenLayout

class SunNodeDetector(BaseObjectDetector):
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur de Plots de Changement de Carte ("Sun Nodes").
    
    Analyse l'image capturée (frame BGR) de la fenêtre de jeu Dofus Unity pour repérer les motifs 
    circulaires dorés/jaunes/verts de changement de carte au sol dans les souterrains et bâtiments.
    """
    def __init__(self, confidence_threshold: float = 0.50, layout: Optional[GameScreenLayout] = None):
        super().__init__(name="sun_node", confidence_threshold=confidence_threshold)
        self.layout = layout or GameScreenLayout()
        
        # Plage HSV 1 : Jaune / Doré vif (motif central & pointes extérieures du soleil)
        self.lower_gold = np.array([15, 60, 60], dtype=np.uint8)
        self.upper_gold = np.array([40, 255, 255], dtype=np.uint8)

        # Plage HSV 2 : Vert / Turquoise lumineux (anneau extérieur du plot de soleil)
        self.lower_green = np.array([41, 50, 50], dtype=np.uint8)
        self.upper_green = np.array([90, 255, 255], dtype=np.uint8)

    def detect(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        return self.detect_sun_nodes(frame)

    def detect_sun_nodes(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Détecte tous les plots de changement de carte ("sun nodes") présents sur le terrain de jeu.
        Exclut la zone HUD supérieure, le chat inférieur, les quêtes et la mini-carte pour éviter les faux positifs.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return {"count": 0, "nodes": [], "found": False}

        h, w = frame.shape[:2]
        
        # Conversion en HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Masque combiné Jaune/Doré + Vert
        mask_gold = cv2.inRange(hsv, self.lower_gold, self.upper_gold)
        mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)
        mask = cv2.bitwise_or(mask_gold, mask_green)

        # Application du masque centralisé de découpage du terrain jouable
        mask = self.layout.apply_to_mask(mask)

        # Nettoyage morphologique
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        nodes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Un plot de soleil a une surface typique entre 40 px² et 8000 px² selon la résolution
            if 40 <= area <= 8000:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                aspect_ratio = float(bw) / bh if bh > 0 else 0
                
                # Le plot au sol forme un ovale ou cercle isométrique (ratio 0.3 à 3.0)
                if 0.3 <= aspect_ratio <= 3.0:
                    confidence = round(min(0.99, 0.50 + (area / 4000.0) * 0.45), 2)
                    nodes.append({
                        "x": int(bx + bw // 2),
                        "y": int(by + bh // 2),
                        "w": int(bw),
                        "h": int(bh),
                        "area": float(area),
                        "confidence": confidence
                    })

        # Fusion des détections très proches (en cas de segmentation partielle du plot)
        filtered_nodes = []
        for node in nodes:
            duplicate = False
            for existing in filtered_nodes:
                dist = np.sqrt((node["x"] - existing["x"])**2 + (node["y"] - existing["y"])**2)
                if dist < 40:  # Moins de 40px de distance -> même plot
                    duplicate = True
                    break
            if not duplicate:
                filtered_nodes.append(node)

        return {
            "object_type": self.name,
            "count": len(filtered_nodes),
            "nodes": filtered_nodes,
            "detections": filtered_nodes,
            "found": len(filtered_nodes) > 0
        }

if __name__ == "__main__":
    detector = SunNodeDetector()
    dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8)
    cv2.circle(dummy_frame, (400, 300), 25, (0, 215, 180), -1)
    res = detector.detect_sun_nodes(dummy_frame)
    print(f"[La Noxine SunNodeDetector] Résultat détection -> {res}")
