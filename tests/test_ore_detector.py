import unittest
import numpy as np
from agents.vision.ore_detector import OreDetector

class TestOreDetector(unittest.TestCase):
    def setUp(self):
        self.detector = OreDetector()

    def test_detect_none_frame(self):
        res = self.detector.detect(None)
        self.assertEqual(res["count"], 0)
        self.assertFalse(res["found"])

    def test_detect_empty_frame(self):
        dummy = np.zeros((300, 300, 3), dtype=np.uint8)
        res = self.detector.detect(dummy)
        self.assertEqual(res["count"], 0)
        self.assertFalse(res["found"])

    def test_detect_copper_ore_synthetic(self):
        # Création d'une image synthétique avec une zone surbrillance/roche cuivrée
        frame = np.zeros((400, 400, 3), dtype=np.uint8)
        # Pixel cuivré BGR (10, 100, 200) -> HSV (approx Hue 13, Sat 240, Val 200)
        frame[150:180, 150:180] = (10, 100, 200)
        res = self.detector.detect(frame)
        self.assertTrue(res["found"])
        self.assertGreaterEqual(res["count"], 1)

if __name__ == "__main__":
    unittest.main()
