import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.dofus_window import DofusWindowController
from agents.motor.bezier_mouse import BezierMouse

def test_focus_window_returns_boolean():
    controller = DofusWindowController()
    res = controller.focus_window()
    assert isinstance(res, bool)

def test_execute_action_calls_focus():
    mouse = BezierMouse()
    executed = []
    def dummy_action(val):
        executed.append(val)
        return val * 2

    res = mouse.execute_action(dummy_action, 5)
    assert res == 10
    assert executed == [5]
