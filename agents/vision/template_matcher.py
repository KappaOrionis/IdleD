try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np

class TemplateMatcher:
    """
    Agent de Perception Visuelle (La Noxine).
    Effectue le Template Matching (avec support CUDA / OpenCV)
    et renvoie les coordonnées et les indices de confiance sans prendre de décision.
    """
    def __init__(self, confidence_threshold=0.8):
        self.confidence_threshold = confidence_threshold

    def match_template(self, frame: np.ndarray, template: np.ndarray):
        """
        Recherche le modèle (template) dans l'image (frame).
        Retourne une liste de détections: [{'x': int, 'y': int, 'w': int, 'h': int, 'confidence': float}]
        """
        if frame is None or template is None:
            return []

        h, w = template.shape[:2]
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.confidence_threshold)
        
        matches = []
        for pt in zip(*loc[::-1]):
            confidence = float(res[pt[1], pt[0]])
            matches.append({
                "x": int(pt[0]),
                "y": int(pt[1]),
                "w": int(w),
                "h": int(h),
                "confidence": round(confidence, 4)
            })
        return matches

if __name__ == "__main__":
    matcher = TemplateMatcher()
    print("[La Noxine] Template Matcher prêt pour l'analyse visuelle.")
