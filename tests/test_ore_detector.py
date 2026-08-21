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

    def test_classify_ore_tooltip_states(self):
        # 1. Épuisé
        res_epuise = OreDetector.classify_ore_tooltip({"resource_name": "Fer", "status": "epuise"})
        self.assertEqual(res_epuise["state"], "epuise")

        # 2. Non minable (niveau mineur requis supérieur au niveau joueur)
        res_locked = OreDetector.classify_ore_tooltip({
            "resource_name": "Argent",
            "required_level": 40,
            "player_level": 20
        })
        self.assertEqual(res_locked["state"], "non_minable")

        # 3. Minable
        res_minable = OreDetector.classify_ore_tooltip({
            "resource_name": "Cuivre",
            "status": "available",
            "required_level": 20,
            "player_level": 50
        })
        self.assertEqual(res_minable["state"], "minable")

    def test_detect_from_differential_frames(self):
        frame_norm = np.zeros((400, 400, 3), dtype=np.uint8)
        frame_high = np.zeros((400, 400, 3), dtype=np.uint8)
        # La frame avec Y a le halo lumineux
        frame_high[150:180, 150:180] = (240, 240, 240)
        res = self.detector.detect_from_differential_frames(frame_norm, frame_high)
        self.assertTrue(res["found"])
        self.assertGreaterEqual(res["count"], 1)

if __name__ == "__main__":
    unittest.main()
