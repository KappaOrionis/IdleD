import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.motor.keyboard_sim import KeyboardSimulator, SCANCODES

def test_keyboard_scancode_lookup():
    kbd = KeyboardSimulator()
    assert 'enter' in SCANCODES
    assert SCANCODES['enter'] == 0x1C
    assert SCANCODES['space'] == 0x39
    assert SCANCODES['/'] == 0x35

def test_keyboard_send_key():
    kbd = KeyboardSimulator(humanize_level=10.0) # Accéléré pour les tests
    # Ne doit pas lever d'exception
    kbd.send_key('a')
    kbd.send_key('enter')

def test_keyboard_type_text():
    kbd = KeyboardSimulator(humanize_level=20.0)
    # Test d'envoi d'une chaîne courte
    kbd.type_text("test")

def test_keyboard_send_unicode():
    kbd = KeyboardSimulator(humanize_level=20.0)
    kbd._send_unicode_char('é')
