import cv2
import numpy as np
from typing import Dict, Any, Optional
from agents.vision.base_detector import BaseObjectDetector
from agents.vision.screen_layout import GameScreenLayout

class OreDetector(BaseObjectDetector):
    """
    Agent de Perception Visuelle (La Noxine) - Détecteur de Gisements de Minerai (Cuivre, Fer, etc.).
    
    Tire parti du mode surbrillance Dofus Unity (Touche 'Y') qui entoure les éléments interactifs
    d'un contour/halo caractéristique, ou détecte directement la texture du gisement de cuivre au sol/paroi.
    """
    def __init__(self, confidence_threshold: float = 0.55, layout: Optional[GameScreenLayout] = None):
        super().__init__(name="copper_ore", confidence_threshold=confidence_threshold)
        self.layout = layout or GameScreenLayout()
        
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

        # Application du masque centralisé de découpage du terrain jouable
        combined_mask = self.layout.apply_to_mask(combined_mask)

        # Nettoyage et fermeture morphologique pour unifier chaque filon
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        closed = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        cleaned = cv2.dilate(closed, kernel_close, iterations=1)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 100:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    cx = int(bx + bw // 2)
                    cy = int(by + bh // 2)

                bx, by, bw, bh = cv2.boundingRect(cnt)
                confidence = round(min(0.99, 0.55 + (area / 5000.0) * 0.44), 2)
                detections.append({
                    "x": cx,
                    "y": cy,
                    "w": int(bw),
                    "h": int(bh),
                    "area": float(area),
                    "confidence": confidence
                })

        # Filtrage des doublons proches
        filtered = []
        for det in sorted(detections, key=lambda d: (d["y"], d["x"])):
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

    def detect_from_differential_frames(self, frame_normal: Optional[np.ndarray], frame_highlight: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Détecte les gisements interactifs par analyse différentielle entre la frame standard (Étape 1)
        et la frame avec surbrillance touche 'Y' (Étape 2), avec calcul du barycentre exact.
        """
        if frame_highlight is None or not isinstance(frame_highlight, np.ndarray) or frame_highlight.size == 0:
            return self.detect(frame_normal)

        if frame_normal is None or not isinstance(frame_normal, np.ndarray) or frame_normal.size == 0:
            return self.detect(frame_highlight)

        # Calcul de la différence absolue entre les deux frames (met en valeur les halos apparus avec 'Y')
        diff = cv2.absdiff(frame_highlight, frame_normal)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh_diff = cv2.threshold(gray_diff, 18, 255, cv2.THRESH_BINARY)

        # Masque couleur classique sur la frame de surbrillance
        hsv = cv2.cvtColor(frame_highlight, cv2.COLOR_BGR2HSV)
        mask_copper = cv2.inRange(hsv, self.lower_copper, self.upper_copper)
        mask_highlight = cv2.inRange(hsv, self.lower_highlight, self.upper_highlight)
        combined_hsv = cv2.bitwise_or(mask_copper, mask_highlight)

        # Combinaison de la différence et de la détection HSV
        combined = cv2.bitwise_or(thresh_diff, combined_hsv)

        # Application du masque centralisé du terrain jouable
        combined = self.layout.apply_to_mask(combined)

        # Fermeture morphologique pour fusionner les contours pointillés d'un même filon
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        cleaned = cv2.dilate(closed, kernel_close, iterations=1)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 100:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    cx = int(bx + bw // 2)
                    cy = int(by + bh // 2)

                bx, by, bw, bh = cv2.boundingRect(cnt)
                confidence = round(min(0.99, 0.60 + (area / 5000.0) * 0.39), 2)
                detections.append({
                    "x": cx,
                    "y": cy,
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

    @staticmethod
    def classify_ore_tooltip(tooltip_data_or_text: Any) -> Dict[str, Any]:
        """
        Classifie l'état d'un filon à partir de son infobulle (Étape 4) :
        - 'epuise' : Filon vide / en cours de repop
        - 'non_minable' : Niveau de mineur insuffisant
        - 'minable' : Prêt à être récolté
        """
        if not tooltip_data_or_text:
            return {"ore_type": "inconnu", "state": "minable", "confidence": 0.50}

        text = ""
        ore_type = "fer"
        status_hint = "available"
        req_level = None
        player_level = None

        if isinstance(tooltip_data_or_text, dict):
            ore_type = str(tooltip_data_or_text.get("resource_name") or tooltip_data_or_text.get("ore_type") or "fer").lower()
            status_hint = str(tooltip_data_or_text.get("status", "available")).lower()
            req_level = tooltip_data_or_text.get("required_level")
            player_level = tooltip_data_or_text.get("player_level")
            text = f"{ore_type} {status_hint} {tooltip_data_or_text.get('raw_text', '')}".lower()
        else:
            text = str(tooltip_data_or_text).lower()
            ore_type = "fer"
            for known in ["fer", "cuivre", "bronze", "kobalte", "manganese", "etain", "argent", "bauxite", "or", "dolomite", "silicate", "obsidienne"]:
                if known in text:
                    ore_type = known
                    break

        # 1. Vérification si Épuisé
        if any(term in text for term in ["epuise", "épuisé", "vide", "depleted", "cooldown", "en attente"]):
            return {
                "ore_type": ore_type,
                "state": "epuise",
                "reason": "Filon vide en cours de réapparition",
                "confidence": 0.95
            }

        # 2. Vérification si Niveau de mineur insuffisant (Non minable)
        if (req_level is not None and player_level is not None and player_level < req_level) or \
           any(term in text for term in ["requis", "insuffisant", "trop bas", "verrouille", "verrouillé", "locked"]):
            return {
                "ore_type": ore_type,
                "state": "non_minable",
                "reason": "Niveau de mineur insuffisant",
                "confidence": 0.92
            }

        # 3. Filon Minable
        return {
            "ore_type": ore_type,
            "state": "minable",
            "reason": "Filon prêt à être récolté",
            "confidence": 0.98
        }
