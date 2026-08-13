import os
import sys
import pytest

# Permet l'import des modules sous agents/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.vision.map_reader import MapHUDReader

def test_map_hud_reader_valid_parsing():
    reader = MapHUDReader()
    # Test avec la capture exacte de Dofus Unity
    result = reader.parse_hud_text("Baie de Sufokia (Sufokia)", "12, 27 - Niveau 10")
    
    assert result["zone_name"] == "Baie de Sufokia (Sufokia)"
    assert result["tile_coords"] == [12, 27]
    assert result["area_level"] == 10

def test_map_hud_reader_negative_coordinates():
    reader = MapHUDReader()
    result = reader.parse_hud_text("Forêt d'Astrub", "-5, -18 - Niveau 20")
    
    assert result["zone_name"] == "Forêt d'Astrub"
    assert result["tile_coords"] == [-5, -18]
    assert result["area_level"] == 20

def test_map_hud_reader_fallback_defaults():
    reader = MapHUDReader()
    result = reader.parse_hud_text("", "Invalid Format")
    
    assert result["zone_name"] == "Inconnue"
    assert result["tile_coords"] == [0, 0]
    assert result["area_level"] == 1
