import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.vision.map_reader import MapHUDReader

def test_map_hud_reader_valid_parsing():
    reader = MapHUDReader()
    result = reader.parse_hud_text("Baie de Sufokia (Sufokia)", "12, 27 - Niveau 10")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Baie de Sufokia (Sufokia)"
    assert result["tile_coords"] == [12, 27]
    assert result["area_level"] == 10
    assert result["error_message"] is None

def test_map_hud_reader_negative_coordinates():
    reader = MapHUDReader()
    result = reader.parse_hud_text("Forêt d'Astrub", "-5, -18 - Niveau 20")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Forêt d'Astrub"
    assert result["tile_coords"] == [-5, -18]
    assert result["area_level"] == 20

def test_map_hud_reader_fallback_defaults():
    reader = MapHUDReader()
    result = reader.parse_hud_text("", "Invalid Format")
    
    assert result["is_detected"] is False
    assert result["zone_name"] == "Détection impossible"
    assert result["tile_coords"] == [None, None]
    assert result["area_level"] is None
    assert result["error_message"] is not None
