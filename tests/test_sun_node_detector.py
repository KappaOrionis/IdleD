import unittest
import numpy as np
import cv2
from agents.vision.sun_node_detector import SunNodeDetector

class TestSunNodeDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SunNodeDetector()

    def test_detect_none_frame(self):
        result = self.detector.detect_sun_nodes(None)
        self.assertEqual(result["count"], 0)
        self.assertFalse(result["found"])
        self.assertEqual(result["nodes"], [])

    def test_detect_empty_frame(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.detector.detect_sun_nodes(frame)
        self.assertEqual(result["count"], 0)
        self.assertFalse(result["found"])

    def test_detect_synthetic_sun_node(self):
        # Création d'une image avec un plot doré/vert de changement de carte
        frame = np.zeros((400, 400, 3), dtype=np.uint8)
        # BGR (0, 200, 180) -> Couleur dorée/verte vive qui entre dans la plage HSV
        cv2.circle(frame, (200, 200), 20, (0, 215, 180), -1)

        result = self.detector.detect_sun_nodes(frame)
        self.assertTrue(result["found"])
        self.assertGreaterEqual(result["count"], 1)
        node = result["nodes"][0]
        self.assertAlmostEqual(node["x"], 200, delta=5)
        self.assertAlmostEqual(node["y"], 200, delta=5)

if __name__ == "__main__":
    unittest.main()
