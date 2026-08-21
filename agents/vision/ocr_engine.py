import cv2
import numpy as np
from typing import Optional, List, Dict, Any, Tuple

class IdleDOCREngine:
    """
    Micro-Agent de Perception Visuelle (La Noxine) - Moteur OCR Robuste (RapidOCR / ONNX Runtime).
    Exécute l'inférence OCR 100% hors-ligne pour la reconnaissance textuelle de :
    - L'en-tête de carte (HUD Zone, Coordonnées, Niveau)
    - Les infobulles (Tooltips) au survol de la souris
    - Les messages de discussion (Chat & Alertes)
    """
    _instance: Optional['IdleDOCREngine'] = None
    _engine = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IdleDOCREngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        """Initialisation paresseuse du moteur RapidOCR ONNX."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()
        except ImportError:
            self._engine = None

    @classmethod
    def get_instance(cls) -> 'IdleDOCREngine':
        if cls._instance is None:
            cls._instance = IdleDOCREngine()
        return cls._instance

    def is_available(self) -> bool:
        return self._engine is not None

    def extract_text(self, image: Optional[np.ndarray]) -> str:
        """
        Extrait le texte brut contenu dans une image (RGB / BGR / Niveaux de gris).
        Retourne une chaîne multi-lignes concaténée.
        """
        lines = self.extract_structured_lines(image)
        return "\n".join([item["text"] for item in lines if item.get("text")])

    def extract_structured_lines(self, image: Optional[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Extrait les lignes de texte structurées avec leur boîte englobante et score de confiance.
        Format retourné : [{"text": str, "confidence": float, "box": list}]
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return []

        if not self.is_available():
            # Fallback en cas d'indisponibilité de la bibliothèque
            return []

        try:
            # Prétraitement : Conversion BGR si nécessaire
            if len(image.shape) == 2:
                img_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                img_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            else:
                img_rgb = image

            result, _elapse = self._engine(img_rgb)
            if not result:
                return []

            structured = []
            for item in result:
                # item format RapidOCR : [box_points, text, confidence]
                if len(item) >= 3:
                    box = item[0]
                    text = str(item[1]).strip()
                    conf = float(item[2])
                    if text:
                        structured.append({
                            "text": text,
                            "confidence": round(conf, 3),
                            "box": box
                        })
            return structured
        except Exception:
            return []

    def inspect_tooltip_crop(self, tooltip_image: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Analyse spécifique pour les infobulles Dofus (nom de l'objet, niveau requis, état épuisé).
        """
        if tooltip_image is None or not isinstance(tooltip_image, np.ndarray) or tooltip_image.size == 0:
            return {
                "raw_text": "",
                "object_name": "inconnu",
                "is_depleted": False,
                "is_insufficient_level": False,
                "level_required": None
            }

        extracted_text = self.extract_text(tooltip_image)
        lower_text = extracted_text.lower()

        is_depleted = "épuisé" in lower_text or "epuise" in lower_text or "(épuisé)" in lower_text
        is_insufficient_level = "insuffisant" in lower_text or "niveau requis" in lower_text or "niveau de métier insuffisant" in lower_text

        return {
            "raw_text": extracted_text,
            "lower_text": lower_text,
            "is_depleted": is_depleted,
            "is_insufficient_level": is_insufficient_level,
            "has_text": len(extracted_text.strip()) > 0
        }
