import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.active_window import ActiveWindowController
from agents.vision.active_capture import ActiveWindowCapture

def test_active_window_controller():
    controller = ActiveWindowController()
    title = controller.get_active_window_title()
    assert isinstance(title, str)

def test_active_window_capture():
    cap = ActiveWindowCapture()
    frame = cap.capture_active_window()
    assert frame is not None
    assert len(frame.shape) == 3
