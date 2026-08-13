import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.vision.tile_tracker import TileTrackerLoop

def test_tile_tracker_lifecycle():
    updated_tiles = []

    def on_tile_changed(data):
        updated_tiles.append(data["tile_coords"])

    tracker = TileTrackerLoop(check_interval_sec=0.1)
    tracker.start(on_tile_changed=on_tile_changed)
    time.sleep(0.3)
    tracker.stop()

    assert len(updated_tiles) >= 1
    assert updated_tiles[0] == [12, 27]
