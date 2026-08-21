import pytest
import numpy as np
from agents.vision.map_analyzer import MapInteractiveAnalyzer

def test_map_analyzer_init():
    analyzer = MapInteractiveAnalyzer()
    assert analyzer is not None
    assert "fer" in analyzer.OBJECT_CATEGORIES
    assert "soleil" in analyzer.OBJECT_CATEGORIES
    assert "ble" in analyzer.OBJECT_CATEGORIES

def test_detect_interactive_zones_empty():
    analyzer = MapInteractiveAnalyzer()
    zones = analyzer.detect_interactive_zones(None, None)
    assert zones == []

def test_detect_interactive_zones_synthetic():
    analyzer = MapInteractiveAnalyzer()
    # Frame 1080p avec un halo lumineux blanc/cyan
    frame_nat = np.zeros((1080, 1920, 3), dtype=np.uint8)
    frame_high = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # Créer un halo interactif au centre de la zone jouable
    frame_high[500:540, 900:950] = [240, 240, 240]

    zones = analyzer.detect_interactive_zones(frame_nat, frame_high)
    assert len(zones) >= 1
    first = zones[0]
    assert 850 <= first["x"] <= 1000
    assert 450 <= first["y"] <= 600

def test_classify_interactive_tooltip():
    # 1. Minerai disponible
    res1 = MapInteractiveAnalyzer.classify_interactive_tooltip("Filon de Fer\nNiveau 1")
    assert res1["object_type"] == "fer"
    assert res1["category"] == "minerai"
    assert res1["state"] == "minable"

    # 2. Minerai épuisé
    res2 = MapInteractiveAnalyzer.classify_interactive_tooltip("Gisement de Cuivre (Épuisé)")
    assert res2["object_type"] == "cuivre"
    assert res2["category"] == "minerai"
    assert res2["state"] == "epuise"

    # 3. Transition plot de soleil
    res3 = MapInteractiveAnalyzer.classify_interactive_tooltip("Changement de carte (Soleil)")
    assert res3["object_type"] == "soleil"
    assert res3["category"] == "transition"

    # 4. Niveau insuffisant
    res4 = MapInteractiveAnalyzer.classify_interactive_tooltip("Filon de Bronze - Niveau de métier insuffisant")
    assert res4["object_type"] == "bronze"
    assert res4["state"] == "non_minable"
