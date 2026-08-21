import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from agents.vision.screen_layout import GameScreenLayout

class MapInteractiveAnalyzer:
    """
    Agent de Perception Visuelle (La Noxine) - Analyseur Universel d'Objets Interactifs.
    
    Identifie tous les objets avec lesquels le joueur peut interagir sur la carte courante :
    1. Analyse différentielle entre la frame naturelle (Étape 1) et la frame avec surbrillance touche 'Y' (Étape 2).
    2. Détection de tous les types d'interactifs :
       - Gisements de Minerai (Fer, Cuivre, Bronze, Kobalte, Or, etc.)
       - Végétaux & Céréales (Blé, Orge, Trèfle, etc.)
       - Arbres (Frêne, Chêne, If, etc.)
       - Poissons & Bancs de pêche
       - Transitions de Carte & Soleils (☀️, Escaliers, Portes, Échelles)
       - Objets de Décor & Quêtes (Leviers, Barils, Coffres, Chariots)
    3. Classification et confirmation de la nature / état via l'infobulle (Tooltip).
    """

    OBJECT_CATEGORIES = {
        # Minerais
        "fer": "minerai", "cuivre": "minerai", "bronze": "minerai", "kobalte": "minerai",
        "manganese": "minerai", "etain": "minerai", "argent": "minerai", "bauxite": "minerai",
        "or": "minerai", "dolomite": "minerai", "silicate": "minerai", "obsidienne": "minerai",
        # Arbres
        "frene": "arbre", "chene": "arbre", "if": "arbre", "erable": "arbre",
        "noyer": "arbre", "merisier": "arbre", "ebene": "arbre", "orme": "arbre",
        # Céréales & Végétaux
        "ble": "cereale", "orge": "cereale", "avoine": "cereale", "houblon": "cereale",
        "lin": "cereale", "seigle": "cereale", "riz": "cereale", "malt": "cereale",
        "trefle": "plante", "menthe": "plante", "orchidee": "plante", "edelweiss": "plante",
        # Transitions
        "soleil": "transition", "porte": "transition", "escalier": "transition",
        "echelle": "transition", "changement_carte": "transition",
        # Éléments de quête / Décor
        "baril": "decor", "levier": "decor", "chariot": "decor", "coffre": "decor", "zaap": "decor"
    }

    def __init__(self, layout: Optional[GameScreenLayout] = None):
        self.layout = layout or GameScreenLayout()
        # Plage HSV de la surbrillance touche 'Y' (Halo lumineux blanc / cyan / doré)
        self.lower_highlight = np.array([0, 0, 185], dtype=np.uint8)
        self.upper_highlight = np.array([180, 70, 255], dtype=np.uint8)

    def detect_interactive_zones(
        self,
        frame_natural: Optional[np.ndarray],
        frame_highlight: Optional[np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Détecte toutes les zones en surbrillance (halo interactif touche 'Y') sur la carte
        et calcule le barycentre exact (centre de masse) de chaque objet interactif.
        """
        if frame_highlight is None or not isinstance(frame_highlight, np.ndarray) or frame_highlight.size == 0:
            if frame_natural is not None and isinstance(frame_natural, np.ndarray) and frame_natural.size > 0:
                hsv_nat = cv2.cvtColor(frame_natural, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv_nat, self.lower_highlight, self.upper_highlight)
            else:
                return []
        elif frame_natural is None or not isinstance(frame_natural, np.ndarray) or frame_natural.size == 0:
            hsv_high = cv2.cvtColor(frame_highlight, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_high, self.lower_highlight, self.upper_highlight)
        else:
            # Différence absolue pour isoler l'effet d'illumination de la touche 'Y'
            diff = cv2.absdiff(frame_highlight, frame_natural)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh_diff = cv2.threshold(gray_diff, 18, 255, cv2.THRESH_BINARY)

            # Masque HSV surbrillance
            hsv = cv2.cvtColor(frame_highlight, cv2.COLOR_BGR2HSV)
            mask_hsv = cv2.inRange(hsv, self.lower_highlight, self.upper_highlight)

            mask = cv2.bitwise_or(thresh_diff, mask_hsv)

        # Découpage du terrain jouable (exclut HUD, chat, sorts, mini-carte)
        mask = self.layout.apply_to_mask(mask)

        # Fermeture et dilatation morphologique pour fusionner les tracés pointillés d'un même filon/objet
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (12, 12))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        cleaned = cv2.dilate(closed, kernel_close, iterations=1)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        zones = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 120:
                # Calcul mathématique précis du barycentre (Moments d'ordre 0 et 1)
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    cx = int(bx + bw // 2)
                    cy = int(by + bh // 2)

                bx, by, bw, bh = cv2.boundingRect(cnt)
                confidence = round(min(0.99, 0.60 + (area / 8000.0) * 0.39), 2)
                zones.append({
                    "x": cx,
                    "y": cy,
                    "w": int(bw),
                    "h": int(bh),
                    "area": float(area),
                    "confidence": confidence,
                    "category": "inconnu",
                    "object_type": "inconnu",
                    "state": "a_confirmer"
                })

        # Tri spatial de haut en bas et filtrage des doublons
        filtered = []
        for z in sorted(zones, key=lambda item: (item["y"], item["x"])):
            duplicate = False
            for existing in filtered:
                dist = np.sqrt((z["x"] - existing["x"])**2 + (z["y"] - existing["y"])**2)
                if dist < 45:
                    duplicate = True
                    break
            if not duplicate:
                filtered.append(z)

        return filtered

    @classmethod
    def classify_interactive_tooltip(cls, tooltip_text_or_data: Any) -> Dict[str, Any]:
        """
        Confirme la nature et l'état d'un objet interactif à partir de son infobulle (Étape 4).
        """
        if not tooltip_text_or_data:
            return {
                "object_type": "inconnu",
                "category": "interactif",
                "state": "minable",
                "label": "Objet Interactif",
                "level_required": 1
            }

        text = ""
        if isinstance(tooltip_text_or_data, str):
            text = tooltip_text_or_data.lower()
        elif isinstance(tooltip_text_or_data, dict):
            text = str(tooltip_text_or_data.get("text", "")).lower() + " " + str(tooltip_text_or_data.get("raw_text", "")).lower()
        else:
            text = str(tooltip_text_or_data).lower()

        # 1. Détection du type d'objet
        detected_type = "inconnu"
        for obj_name in cls.OBJECT_CATEGORIES.keys():
            if obj_name in text:
                detected_type = obj_name
                break

        # Catégorie
        category = cls.OBJECT_CATEGORIES.get(detected_type, "interactif")

        # 2. Détection de l'état
        if any(w in text for w in ["épuisé", "epuise", "vide", "en repousse", "0 restant", "fauché", "coupe", "recolte"]):
            state = "epuise"
        elif any(w in text for w in ["insuffisant", "requis", "niveau trop bas", "verrouillé", "bloqué", "ferme"]):
            state = "non_minable"
        elif any(w in text for w in ["changement", "carte", "soleil", "entrer", "sortir", "monter", "descendre"]):
            state = "transition"
        else:
            state = "minable"

        label = detected_type.capitalize() if detected_type != "inconnu" else "Objet Interactif"

        return {
            "object_type": detected_type,
            "category": category,
            "state": state,
            "label": label,
            "raw_tooltip": text[:80]
        }

    @classmethod
    def inspect_tooltip_image(cls, tooltip_image: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Analyse une nouvelle image capturée sous le curseur via le moteur OCR RapidOCR (Étape 4).
        """
        if tooltip_image is None or not isinstance(tooltip_image, np.ndarray) or tooltip_image.size == 0:
            return cls.classify_interactive_tooltip("")

        from agents.vision.ocr_engine import IdleDOCREngine
        ocr = IdleDOCREngine.get_instance()
        text = ocr.extract_text(tooltip_image)
        return cls.classify_interactive_tooltip(text)
