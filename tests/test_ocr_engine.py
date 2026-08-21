import pytest
import numpy as np
import cv2
from agents.vision.ocr_engine import IdleDOCREngine
from agents.vision.map_analyzer import MapInteractiveAnalyzer

def test_ocr_engine_singleton_init():
    ocr1 = IdleDOCREngine.get_instance()
    ocr2 = IdleDOCREngine()
    assert ocr1 is ocr2
    assert ocr1.is_available() is True

def test_ocr_engine_empty_input():
    ocr = IdleDOCREngine.get_instance()
    assert ocr.extract_text(None) == ""
    assert ocr.extract_text(np.zeros((0, 0, 3), dtype=np.uint8)) == ""
    assert ocr.extract_structured_lines(None) == []

def test_ocr_engine_synthetic_text():
    ocr = IdleDOCREngine.get_instance()
    # Image blanche avec texte noir
    img = np.ones((80, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Filon de Fer", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    extracted = ocr.extract_text(img)
    assert len(extracted) > 0
    assert "fer" in extracted.lower() or "filon" in extracted.lower()

def test_ocr_tooltip_inspection_synthetic():
    ocr = IdleDOCREngine.get_instance()
    # Image sombre d'infobulle avec texte blanc
    img = np.zeros((80, 320, 3), dtype=np.uint8)
    cv2.putText(img, "Filon de Cuivre (Epuise)", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    res = ocr.inspect_tooltip_crop(img)
    assert res["has_text"] is True

def test_map_analyzer_inspect_tooltip_image():
    # Test d'intégration directe avec MapInteractiveAnalyzer
    img = np.zeros((80, 300, 3), dtype=np.uint8)
    cv2.putText(img, "Filon de Bronze", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    analysis = MapInteractiveAnalyzer.inspect_tooltip_image(img)
    assert "object_type" in analysis
    assert "category" in analysis
    assert "state" in analysis
