import pytest
import numpy as np
from agents.vision.screen_layout import GameScreenLayout

def test_screen_layout_dimensions():
    layout = GameScreenLayout()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mask = layout.get_playable_area_mask(frame)
    
    assert mask.shape == (1080, 1920)
    assert mask.dtype == np.uint8

def test_screen_layout_ui_exclusion():
    layout = GameScreenLayout(quest_panel_open=True, minimap_open=True)
    frame = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    mask = layout.get_playable_area_mask(frame)

    # 1. Haut gauche (HUD Carte) doit être masqué (0)
    assert mask[20, 50] == 0
    
    # 2. Volet des quêtes (Milieu Gauche) doit être masqué (0)
    assert mask[300, 50] == 0

    # 3. Chat (Bas Gauche) doit être masqué (0)
    assert mask[850, 50] == 0

    # 4. Cœur / Barre sorts (Bas Centre) doit être masqué (0)
    assert mask[850, 500] == 0

    # 5. Mini-carte (Bas Droite) doit être masquée (0)
    assert mask[850, 800] == 0

    # 6. Bord Droit (Barre icônes) doit être masqué (0)
    assert mask[500, 985] == 0

    # 7. Terrain de jeu actif (Centre) doit être conservé (255)
    assert mask[400, 500] == 255
    assert mask[300, 700] == 255

def test_screen_layout_collapsed_quest_panel():
    layout_closed = GameScreenLayout(quest_panel_open=False)
    frame = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
    mask_closed = layout_closed.get_playable_area_mask(frame)

    # Lorsque le volet des quêtes est fermé, la zone milieu gauche devient jouable (255)
    assert mask_closed[300, 50] == 255

def test_screen_layout_hud_crop():
    frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
    crop = GameScreenLayout.get_hud_map_crop(frame)
    
    assert crop.shape[0] == 85  # 8.5% de 1000
    assert crop.shape[1] == 260 # 26% de 1000
