import ctypes
from ctypes import wintypes
import random
import time
from typing import Optional, Dict
from agents.motor.active_window import ActiveWindowController
from agents.motor.pid_sim import PIDDeviceIdentity

# DirectInput Hardware Scancodes (Set 1 standard physique)
SCANCODES = {
    'enter': 0x1C,
    '\n': 0x1C,
    'space': 0x39,
    ' ': 0x39,
    'slash': 0x35,
    '/': 0x35,
    'comma': 0x33,
    ',': 0x33,
    'backspace': 0x0E,
    'tab': 0x0F,
    'esc': 0x01,
    'up': 0x48,
    'down': 0x50,
    'left': 0x4B,
    'right': 0x4D,
    'a': 0x10, 'z': 0x11, 'e': 0x12, 'r': 0x13, 't': 0x14, 'y': 0x15,
    'u': 0x16, 'i': 0x17, 'o': 0x18, 'p': 0x19, 'q': 0x1E, 's': 0x1F,
    'd': 0x20, 'f': 0x21, 'g': 0x22, 'h': 0x23, 'j': 0x24, 'k': 0x25,
    'l': 0x26, 'm': 0x27, 'w': 0x2C, 'x': 0x2D, 'c': 0x2E, 'v': 0x2F,
    'b': 0x30, 'n': 0x31,
    '0': 0x0B, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05,
    '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A
}

# Structures Win32 pour l'API SendInput (simulation matérielle réelle niveau OS)
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL)
    ]

class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ii", Input_I)
    ]

INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

class KeyboardSimulator:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Saisie Clavier Matérielle & Périphérique Réel (SendInput).
    Injecte des événements physiques réels dans la fenêtre active au premier plan avec:
    - Scancodes matériels directs (Set 1) et support Unicode natif
    - Délais et temps de maintien distribués selon une Gaussienne (Loi de Fitts / Biomecanique)
    - Indépendance totale vis-à-vis d'un processus spécifique.
    """
    def __init__(self, humanize_level: float = 1.0, preset_key: str = "logitech_g915_tkl"):
        self.user32 = ctypes.windll.user32
        self.humanize_level = max(0.1, humanize_level)
        self.active_window = ActiveWindowController()
        self.device_identity = PIDDeviceIdentity(preset_key)

    def _send_hardware_input(self, scancode: int, is_up: bool = False):
        """Envoie un événement de touche matérielle directe via SendInput OS."""
        flags = KEYEVENTF_SCANCODE
        if is_up:
            flags |= KEYEVENTF_KEYUP

        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, scancode, flags, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
        self.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def _send_unicode_char(self, char: str):
        """Envoie un caractère Unicode physique direct via SendInput OS."""
        extra = ctypes.c_ulong(0)
        code = ord(char)
        
        # KeyDown
        ii_down = Input_I()
        ii_down.ki = KeyBdInput(0, code, KEYEVENTF_UNICODE, 0, ctypes.pointer(extra))
        x_down = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_down)
        self.user32.SendInput(1, ctypes.pointer(x_down), ctypes.sizeof(x_down))

        time.sleep(max(0.02, random.gauss(0.04, 0.01)) / self.humanize_level)

        # KeyUp
        ii_up = Input_I()
        ii_up.ki = KeyBdInput(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x_up = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_up)
        self.user32.SendInput(1, ctypes.pointer(x_up), ctypes.sizeof(x_up))

    def send_key(self, key_name: str, hold_mean_sec: float = 0.055, hold_dev_sec: float = 0.015):
        """
        Enfonce et relâche une touche matérielle physique (KeyDown -> Sleep -> KeyUp).
        """
        key_lower = key_name.lower()
        scancode = SCANCODES.get(key_lower)
        
        if scancode is None:
            if len(key_name) == 1:
                self._send_unicode_char(key_name)
                return
            scancode = 0x1C  # Par défaut Entrée

        # Pression (KeyDown)
        self._send_hardware_input(scancode, is_up=False)

        # Temps de maintien réaliste (~55ms)
        hold_time = max(0.025, random.gauss(hold_mean_sec, hold_dev_sec)) / self.humanize_level
        time.sleep(hold_time)

        # Relâchement (KeyUp)
        self._send_hardware_input(scancode, is_up=True)

    def type_text(self, text: str, interkey_mean_sec: float = 0.065, interkey_dev_sec: float = 0.02):
        """
        Tape une chaîne de caractères dans la fenêtre active exactement comme un périphérique matériel.
        """
        for char in text:
            scancode = SCANCODES.get(char.lower())
            if scancode is not None:
                self.send_key(char)
            else:
                self._send_unicode_char(char)

            delay = max(0.025, random.gauss(interkey_mean_sec, interkey_dev_sec)) / self.humanize_level
            time.sleep(delay)

    def type_text_into_active_window(self, text: str) -> bool:
        """
        Injecte directement le texte dans la fenêtre actuellement active au premier plan (Foreground Window).
        """
        title = self.active_window.get_active_window_title()
        print(f"[Le Scaphandre Keyboard] Injection matérielle de '{text}' dans la fenêtre active ('{title}')...")
        self.type_text(text)
        return True

    def send_chat_message(self, message: str) -> bool:
        """
        Envoie un message/commande dans la fenêtre active (Entrée -> Texte -> Entrée).
        """
        self.send_key('enter')
        time.sleep(random.uniform(0.12, 0.22))
        self.type_text(message)
        time.sleep(random.uniform(0.08, 0.18))
        self.send_key('enter')
        return True

if __name__ == "__main__":
    kbd = KeyboardSimulator()
    print("[Le Scaphandre] Clavier matériel initialisé.")
