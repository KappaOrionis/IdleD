import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.keyboard_sim import KeyboardSimulator

def test_keyboard_scancode_lookup():
    kbd = KeyboardSimulator()
    assert 'enter' in kbd.SCANCODES
    assert kbd.SCANCODES['enter'] == 0x1C
    assert kbd.SCANCODES['space'] == 0x39
    assert kbd.SCANCODES['/'] == 0x35

def test_keyboard_send_key():
    kbd = KeyboardSimulator(humanize_level=10.0) # Accéléré pour les tests
    # Ne doit pas lever d'exception
    kbd.send_key('a')
    kbd.send_key('enter')

def test_keyboard_type_text():
    kbd = KeyboardSimulator(humanize_level=20.0)
    # Test d'envoi d'une chaîne courte
    kbd.type_text("test")
