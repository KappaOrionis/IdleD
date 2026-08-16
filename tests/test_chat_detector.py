import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.vision.chat_detector import ChatDetector

def test_chat_detector_basic():
    detector = ChatDetector()
    res = detector.detect_chat_input_box(None, (100, 100, 1280, 720))
    assert res["found"] is True
    assert res["confidence"] > 0.9
    assert res["bounding_box"]["width"] > 0
    assert res["bounding_box"]["height"] > 0
    assert len(res["click_target"]) == 2

def test_chat_detector_calibrated_position_1080p():
    detector = ChatDetector()
    # Résolution 1920x1080 Full HD
    res = detector.detect_chat_input_box(None, (0, 0, 1920, 1080))
    cx, cy = res["click_target"]
    # Sur 1080p, la boîte de saisie chat est au bas gauche :
    # X ~ 50 à 450 px
    # Y ~ 1040 à 1075 px
    assert 50 < cx < 450
    assert 1030 < cy < 1080

def test_chat_detector_with_frame():
    detector = ChatDetector()
    # Image synthétique sombre (comme le fond du chat)
    dark_frame = np.full((1080, 1920, 3), 25, dtype=np.uint8)
    res = detector.detect_chat_input_box(dark_frame, (0, 0, 1920, 1080))
    assert res["found"] is True
    assert res["confidence"] >= 0.98
