import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.pid_sim import PIDController, PIDMouseTrajectory, PIDDeviceIdentity, POPULAR_HARDWARE_PRESETS

def test_pid_controller_convergence():
    pid = PIDController(kp=5.0, ki=0.5, kd=0.1, out_min=-500.0, out_max=500.0)
    current = 0.0
    target = 100.0
    for _ in range(100):
        output = pid.update(target, current, dt=0.02)
        current += output * 0.02

    assert abs(target - current) < 5.0

def test_pid_mouse_trajectory():
    traj = PIDMouseTrajectory()
    pts = traj.generate_points((0, 0), (200, 150))
    assert len(pts) > 5
    assert pts[0] == (0, 0)
    assert pts[-1] == (200, 150)

def test_pid_device_identity():
    device = PIDDeviceIdentity("logitech_g502_hero")
    sig = device.get_hardware_signature()
    assert sig["is_hardware_pid_simulated"] is True
    assert sig["vid"] == "0x046D"
    assert sig["pid"] == "0xC08B"
    assert "Logitech" in sig["vendor"]

def test_popular_presets_catalog():
    presets = PIDDeviceIdentity.list_available_presets()
    assert "logitech_g502_hero" in presets
    assert "razer_deathadder_v3" in presets
    assert "corsair_k70_mk2" in presets
    assert "steelseries_apex_pro" in presets

def test_gaming_bundle_creation():
    mouse, kbd = PIDDeviceIdentity.create_gaming_bundle("razer")
    assert mouse.vendor == "Razer Inc."
    assert kbd.vendor == "Razer Inc."
    assert mouse.product_id == 0x00B6
    assert kbd.product_id == 0x0256
