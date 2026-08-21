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

def test_map_hud_reader_user_example_coordinates():
    reader = MapHUDReader()
    # Test avec la syntaxe exacte fournie par l'utilisateur: "7, -19"
    result = reader.parse_hud_text("Amakna", "7, -19")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Amakna"
    assert result["tile_coords"] == [7, -19]
    assert result["area_level"] is None
    assert result["error_message"] is None

def test_map_hud_reader_user_example_astrub_zone():
    reader = MapHUDReader()
    # Test avec la syntaxe exacte fournie par l'utilisateur: "Astrub (Cité d'Astrub)" et "7, -19"
    result = reader.parse_hud_text("Astrub (Cité d'Astrub)", "7, -19")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Astrub (Cité d'Astrub)"
    assert result["tile_coords"] == [7, -19]
    assert result["area_level"] is None
    assert result["error_message"] is None

def test_map_hud_reader_user_example_complete_hud():
    reader = MapHUDReader()
    # Test combinant les 3 exemples réels fournis par l'utilisateur:
    # 1. Zone : "Astrub (Cité d'Astrub)"
    # 2. Coordonnées : "7, -19"
    # 3. Niveau : "Niveau 10"
    result = reader.parse_hud_text("Astrub (Cité d'Astrub)", "7, -19 - Niveau 10")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Astrub (Cité d'Astrub)"
    assert result["tile_coords"] == [7, -19]
    assert result["area_level"] == 10
    assert result["error_message"] is None

def test_map_hud_reader_pandala_bonus_goal():
    reader = MapHUDReader()
    # Test pour l'objectif utilisateur: "25, -29 - Niveau 100 61%" sur "Île de Pandala (Plantala)"
    result = reader.parse_hud_text("Île de Pandala (Plantala)", "25, -29 - Niveau 100 61%\n[LPM]")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Île de Pandala (Plantala)"
    assert result["tile_coords"] == [25, -29]
    assert result["area_level"] == 100
    assert result["zone_bonus"] == "61%"
    assert result["error_message"] is None

def test_map_hud_reader_invalid_or_loading():
    reader = MapHUDReader()
    result = reader.parse_hud_text(None, None)
    
    assert result["is_detected"] is False
    assert result["zone_name"] is None
    assert result["tile_coords"] == [None, None]
    assert result["error_message"] is not None
    assert result["error_message"] is not None

def test_map_hud_reader_mine_istairameur():
    reader = MapHUDReader()
    # Test pour le cas réel de la Mine Istairameur : "Mine Istairameur" et "-3, 9"
    result = reader.parse_hud_text("Mine Istairameur", "-3, 9")
    
    assert result["is_detected"] is True
    assert result["zone_name"] == "Mine Istairameur"
    assert result["tile_coords"] == [-3, 9]
    assert result["error_message"] is None

def test_map_hud_reader_fallback_defaults():
    reader = MapHUDReader()
    result = reader.parse_hud_text("", "Invalid Format")
    
    assert result["is_detected"] is False
    assert result["zone_name"] == "Détection impossible"
    assert result["tile_coords"] == [None, None]
    assert result["area_level"] is None
    assert result["error_message"] is not None
