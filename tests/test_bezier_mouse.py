import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.bezier_mouse import BezierMouse

def test_bezier_trajectory_generation():
    mouse = BezierMouse()
    start = (100, 100)
    end = (400, 300)
    steps = 20
    
    trajectory = mouse.generate_trajectory(start, end, steps=steps)
    
    assert len(trajectory) == steps + 1
    assert trajectory[0] == start
    assert trajectory[-1] == end
