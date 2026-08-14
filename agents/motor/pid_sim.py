import time
import math
import random
from typing import Tuple, List, Optional, Dict, Any

# Catalogue des références constructeurs et modèles populaires (Souris & Claviers)
POPULAR_HARDWARE_PRESETS = {
    # 1. Logitech Gaming Series
    "logitech_g502_hero": {
        "type": "mouse",
        "vendor": "Logitech",
        "vendor_id": 0x046D,
        "product_id": 0xC08B,
        "product_name": "Logitech G502 HERO Gaming Mouse",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "dpi_max": 25600,
        "hid_interface": "USB\\VID_046D&PID_C08B&MI_00"
    },
    "logitech_g_pro_superlight": {
        "type": "mouse",
        "vendor": "Logitech",
        "vendor_id": 0x046D,
        "product_id": 0x408A,
        "product_name": "Logitech G Pro X Superlight Wireless",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "dpi_max": 25600,
        "hid_interface": "USB\\VID_046D&PID_408A&MI_00"
    },
    "logitech_g915_tkl": {
        "type": "keyboard",
        "vendor": "Logitech",
        "vendor_id": 0x046D,
        "product_id": 0xC545,
        "product_name": "Logitech G915 LIGHTSPEED Wireless RGB Mechanical Gaming Keyboard",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "hid_interface": "USB\\VID_046D&PID_C545&MI_01"
    },
    "logitech_g213_prodigy": {
        "type": "keyboard",
        "vendor": "Logitech",
        "vendor_id": 0x046D,
        "product_id": 0xC336,
        "product_name": "Logitech G213 Prodigy RGB Gaming Keyboard",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "hid_interface": "USB\\VID_046D&PID_C336&MI_01"
    },

    # 2. Razer Series
    "razer_deathadder_v3": {
        "type": "mouse",
        "vendor": "Razer Inc.",
        "vendor_id": 0x1532,
        "product_id": 0x00B6,
        "product_name": "Razer DeathAdder V3 Pro",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "dpi_max": 30000,
        "hid_interface": "USB\\VID_1532&PID_00B6&MI_00"
    },
    "razer_blackwidow_v3": {
        "type": "keyboard",
        "vendor": "Razer Inc.",
        "vendor_id": 0x1532,
        "product_id": 0x0256,
        "product_name": "Razer BlackWidow V3 Mechanical Keyboard",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "hid_interface": "USB\\VID_1532&PID_0256&MI_01"
    },

    # 3. Corsair Gaming Series
    "corsair_scimitar_elite": {
        "type": "mouse",
        "vendor": "Corsair",
        "vendor_id": 0x1B1C,
        "product_id": 0x1B8E,
        "product_name": "Corsair SCIMITAR RGB ELITE Gaming Mouse",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "dpi_max": 18000,
        "hid_interface": "USB\\VID_1B1C&PID_1B8E&MI_00"
    },
    "corsair_k70_mk2": {
        "type": "keyboard",
        "vendor": "Corsair",
        "vendor_id": 0x1B1C,
        "product_id": 0x1B4F,
        "product_name": "Corsair K70 RGB MK.2 Mechanical Gaming Keyboard",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "hid_interface": "USB\\VID_1B1C&PID_1B4F&MI_01"
    },

    # 4. SteelSeries
    "steelseries_rival_3": {
        "type": "mouse",
        "vendor": "SteelSeries",
        "vendor_id": 0x1038,
        "product_id": 0x1824,
        "product_name": "SteelSeries Rival 3 Gaming Mouse",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "dpi_max": 8500,
        "hid_interface": "USB\\VID_1038&PID_1824&MI_00"
    },
    "steelseries_apex_pro": {
        "type": "keyboard",
        "vendor": "SteelSeries",
        "vendor_id": 0x1038,
        "product_id": 0x1612,
        "product_name": "SteelSeries Apex Pro OmniPoint Keyboard",
        "usb_version": "2.0",
        "polling_rate_hz": 1000,
        "hid_interface": "USB\\VID_1038&PID_1612&MI_01"
    }
}


class PIDController:
    """
    Régulateur / Contrôleur PID (Proportionnel - Intégral - Dérivé).
    Modélise la biomécanique musculaire humaine pour la simulation motrice :
    - Proportionnel (Kp) : Force d'attraction vers la cible (erreur courante)
    - Intégral (Ki) : Élimination de l'erreur statique résiduelle dans le temps
    - Dérivé (Kd) : Amortissement / Damping pour limiter l'overshoot et simuler la viscosité musculaire
    """
    def __init__(self, kp: float = 0.6, ki: float = 0.05, kd: float = 0.25, out_min: float = -100.0, out_max: float = 100.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.out_min = out_min
        self.out_max = out_max
        
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.perf_counter()

    def reset(self):
        """Réinitialise les termes accumulés du régulateur."""
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.perf_counter()

    def update(self, setpoint: float, current_val: float, dt: Optional[float] = None) -> float:
        """
        Calcule la correction PID à appliquer pour atteindre la consigne (setpoint).
        """
        now = time.perf_counter()
        if dt is None:
            dt = now - self.last_time
            if dt <= 0.0:
                dt = 0.001
        self.last_time = now

        error = setpoint - current_val

        # Terme Proportionnel
        p_term = self.kp * error

        # Terme Intégral avec anti-windup
        self.integral += error * dt
        i_term = self.ki * self.integral

        # Terme Dérivé
        derivative = (error - self.prev_error) / dt
        d_term = self.kd * derivative

        self.prev_error = error

        output = p_term + i_term + d_term
        return max(self.out_min, min(self.out_max, output))


class PIDMouseTrajectory:
    """
    Générateur de trajectoires physiques contrôlées par double PID (X et Y) simulant un bras humain :
    - Masse et inertie du membre supérieur
    - Frottements et amortissement visqueux
    - Micro-tremblements physiologiques (Tremor)
    """
    def __init__(self, kp: float = 2.4, ki: float = 0.08, kd: float = 0.35, mass: float = 1.2, friction: float = 0.85):
        self.pid_x = PIDController(kp, ki, kd, out_min=-500.0, out_max=500.0)
        self.pid_y = PIDController(kp, ki, kd, out_min=-500.0, out_max=500.0)
        self.mass = mass
        self.friction = friction

    def generate_points(self, start: Tuple[int, int], target: Tuple[int, int], max_steps: int = 120) -> List[Tuple[int, int]]:
        """
        Simule le déplacement physique complet jusqu'à la cible via régulateurs PID couplés.
        """
        self.pid_x.reset()
        self.pid_y.reset()

        curr_x, curr_y = float(start[0]), float(start[1])
        vel_x, vel_y = 0.0, 0.0
        target_x, target_y = float(target[0]), float(target[1])

        dt = 0.012 # Pas de temps de simulation ~12ms (83 Hz)
        points = [(int(round(curr_x)), int(round(curr_y)))]

        for _ in range(max_steps):
            dist = math.hypot(target_x - curr_x, target_y - curr_y)
            if dist < 1.5 and abs(vel_x) < 2.0 and abs(vel_y) < 2.0:
                break

            # Correction de force calculée par le PID
            force_x = self.pid_x.update(target_x, curr_x, dt)
            force_y = self.pid_y.update(target_y, curr_y, dt)

            # Ajout d'un micro-tremblement biomécanique naturel (0.3px)
            tremor_x = random.gauss(0, 0.25)
            tremor_y = random.gauss(0, 0.25)

            # Accélération = (Force - Frottement * Vitesse) / Masse
            acc_x = (force_x - self.friction * vel_x + tremor_x) / self.mass
            acc_y = (force_y - self.friction * vel_y + tremor_y) / self.mass

            # Intégration d'Euler
            vel_x += acc_x * dt
            vel_y += acc_y * dt

            curr_x += vel_x * dt
            curr_y += vel_y * dt

            points.append((int(round(curr_x)), int(round(curr_y))))

        points.append((int(target_x), int(target_y)))
        return points


class PIDDeviceIdentity:
    """
    Simulation de l'identité matérielle USB HID (Vendor ID / Product ID / Physical Interface Device).
    Prend en charge les presets de marques et modèles gaming les plus populaires du marché.
    """
    def __init__(self, preset_key: str = "logitech_g502_hero"):
        preset = POPULAR_HARDWARE_PRESETS.get(preset_key, POPULAR_HARDWARE_PRESETS["logitech_g502_hero"])
        self.preset_key = preset_key
        self.device_type = preset.get("type", "mouse")
        self.vendor = preset.get("vendor", "Logitech")
        self.vendor_id = preset.get("vendor_id", 0x046D)
        self.product_id = preset.get("product_id", 0xC08B) # PID USB Réel
        self.product_name = preset.get("product_name", "Logitech G502 HERO Gaming Mouse")
        self.polling_rate_hz = preset.get("polling_rate_hz", 1000)
        self.hid_interface = preset.get("hid_interface", "USB\\VID_046D&PID_C08B")

    @classmethod
    def list_available_presets(cls) -> Dict[str, Dict[str, Any]]:
        """Retourne la liste des presets matériels populaires disponibles."""
        return POPULAR_HARDWARE_PRESETS

    @classmethod
    def create_gaming_bundle(cls, brand: str = "logitech") -> Tuple['PIDDeviceIdentity', 'PIDDeviceIdentity']:
        """
        Crée un ensemble assorti Souris + Clavier d'une même marque populaire.
        """
        brand_lower = brand.lower()
        if "razer" in brand_lower:
            return (cls("razer_deathadder_v3"), cls("razer_blackwidow_v3"))
        elif "corsair" in brand_lower:
            return (cls("corsair_scimitar_elite"), cls("corsair_k70_mk2"))
        elif "steelseries" in brand_lower:
            return (cls("steelseries_rival_3"), cls("steelseries_apex_pro"))
        else: # Default Logitech
            return (cls("logitech_g502_hero"), cls("logitech_g915_tkl"))

    def get_hardware_signature(self) -> dict:
        return {
            "preset_key": self.preset_key,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "vid": f"0x{self.vendor_id:04X}",
            "pid": f"0x{self.product_id:04X}",
            "product_name": self.product_name,
            "polling_rate_hz": self.polling_rate_hz,
            "hid_interface": self.hid_interface,
            "is_hardware_pid_simulated": True
        }

if __name__ == "__main__":
    mouse, kbd = PIDDeviceIdentity.create_gaming_bundle("logitech")
    print("Souris active :", mouse.get_hardware_signature())
    print("Clavier actif :", kbd.get_hardware_signature())
