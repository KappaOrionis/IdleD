import unittest
import numpy as np
from agents.vision.base_detector import BaseObjectDetector
from agents.vision.object_registry import VisionObjectRegistry

class DummyDetector(BaseObjectDetector):
    def __init__(self, name: str):
        super().__init__(name=name)

    def detect(self, frame):
        return {
            "object_type": self.name,
            "count": 1,
            "detections": [{"x": 10, "y": 20, "w": 30, "h": 40}],
            "found": True
        }

class TestVisionObjectRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = VisionObjectRegistry()

    def test_default_registration(self):
        detector = self.registry.get_detector("sun_node")
        self.assertIsNotNone(detector)
        self.assertEqual(detector.name, "sun_node")

    def test_custom_detector_registration(self):
        dummy = DummyDetector("zaap")
        self.registry.register_detector(dummy)
        
        retrieved = self.registry.get_detector("zaap")
        self.assertIsNotNone(retrieved)
        
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        results = self.registry.analyze_all_objects(dummy_frame)
        self.assertIn("zaap", results)
        self.assertEqual(results["zaap"]["count"], 1)

if __name__ == "__main__":
    unittest.main()
