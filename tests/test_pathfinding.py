import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.brain.pathfinding import PathfindingEngine

def test_pathfinding_same_start_and_target():
    engine = PathfindingEngine()
    path = engine.find_path((0, 0), (0, 0))
    assert path == [(0, 0)]

def test_pathfinding_straight_line():
    engine = PathfindingEngine()
    path = engine.find_path((0, 0), (3, 0))
    assert path == [(0, 0), (1, 0), (2, 0), (3, 0)]

def test_pathfinding_manhattan_steps():
    engine = PathfindingEngine()
    path = engine.find_path((10, 10), (12, 11))
    assert len(path) == 4
    assert path[0] == (10, 10)
    assert path[-1] == (12, 11)
