import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.dofus_window import DofusWindowController

def test_dofus_window_controller_initialization():
    controller = DofusWindowController()
    assert controller.window_title_keyword == "dofus"
    hwnd = controller.find_window()
    assert hwnd is None or isinstance(hwnd, int)

def test_client_to_screen_fallback():
    controller = DofusWindowController()
    coords = controller.client_to_screen(100, 200)
    assert coords is None or isinstance(coords, tuple)
