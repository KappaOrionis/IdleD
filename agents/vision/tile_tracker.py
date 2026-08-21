import os
import sys
import time
import threading
from typing import Callable, Optional, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.vision.screen_capture import ScreenCapture
from agents.vision.map_reader import MapHUDReader
from agents.vision.object_registry import VisionObjectRegistry

class TileTrackerLoop:
    """
    Agent de Perception Visuelle (La Noxine) - Boucle de Suivi de Tuile Temps Réel.
    Exécute une capture vidéo en boucle fermée et alerte dès que les coordonnées
    de la tuile [x, y], la zone, le niveau ou les objets détectés à l'écran changent.
    """
    def __init__(self, check_interval_sec: float = 0.5):
        self.check_interval = check_interval_sec
        self.screen_capture = ScreenCapture()
        self.map_reader = MapHUDReader()
        self.object_registry = VisionObjectRegistry()
        self.current_tile_data: Optional[Dict[str, Any]] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.on_tile_changed_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def start(self, on_tile_changed: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Démarre la boucle de détection de tuile en arrière-plan.
        """
        if self.running:
            return

        self.on_tile_changed_callback = on_tile_changed
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("[La Noxine TileTracker] Boucle de suivi temps réel démarrée.")

    def stop(self):
        """
        Arrête la boucle de détection.
        """
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[La Noxine TileTracker] Boucle de suivi arrêtée.")

    def _monitor_loop(self):
        while self.running:
            has_active_window = bool(self.screen_capture.window_controller.get_active_hwnd())

            if not has_active_window:
                latest_data = self.map_reader.parse_hud_text("", "")
                latest_data["sun_nodes_count"] = 0
                latest_data["detected_objects"] = {}
            else:
                frame = self.screen_capture.capture_frame()
                objects_summary = self.object_registry.analyze_all_objects(frame)
                
                latest_data = self.map_reader.extract_from_frame(frame)
                sun_info = objects_summary.get("sun_node", {})
                latest_data["sun_nodes_count"] = sun_info.get("count", 0)
                latest_data["detected_objects"] = objects_summary

            # Vérification du changement d'état ou de tuile
            if self.current_tile_data != latest_data:
                self.current_tile_data = latest_data
                if latest_data["is_detected"]:
                    print(f"[La Noxine TileTracker] Tuile active détectée : {latest_data['tile_coords']} dans {latest_data['zone_name']}")
                else:
                    print(f"[La Noxine TileTracker] Échec détection : {latest_data['error_message']}")

                if self.on_tile_changed_callback:
                    self.on_tile_changed_callback(latest_data)

            time.sleep(self.check_interval)

if __name__ == "__main__":
    def handle_tile_change(data):
        print(f"[CALLBACK IPC] Statut tuile -> {data}")

    tracker = TileTrackerLoop(check_interval_sec=0.2)
    tracker.start(on_tile_changed=handle_tile_change)
    time.sleep(0.5)
    tracker.stop()
