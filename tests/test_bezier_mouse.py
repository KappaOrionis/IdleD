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
    
    # Trajectoire générée doit contenir au minimum les étapes et atteindre la destination
    assert len(trajectory) >= steps + 1
    assert trajectory[0] == start
    assert trajectory[-1] == end

def test_bezier_fitts_law_dynamic_steps():
    mouse = BezierMouse()
    short_traj = mouse.generate_trajectory((0, 0), (50, 50))
    long_traj = mouse.generate_trajectory((0, 0), (1000, 1000))
    
    # Un trajet long doit comporter plus de micro-étapes qu'un trajet court
    assert len(long_traj) > len(short_traj)

def test_cursor_pos_reading():
    mouse = BezierMouse()
    pos = mouse.get_current_cursor_pos()
    assert isinstance(pos, tuple)
    assert len(pos) == 2
