import ctypes
import random
import time
from typing import Optional, Dict

class KeyboardSimulator:
    """
    Agent d'Exécution Motrice (Le Scaphandre) - Saisie Clavier Humanisée & DirectInput.
    Génère des frappes clavier au niveau système d'exploitation avec:
    - Scancodes matériels Windows Win32 (DirectInput / SendInput) compatibles Dofus Unity
    - Délais inter-touches distribués selon une Gaussienne (Loi de Fitts / Biomecanique)
    - Temps d'enfoncement (Key Hold Time) variable et réaliste
    """
    # Mappage des Scancodes matériels standard US/FR pour DirectInput
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
        'a': 0x1E, 'b': 0x30, 'c': 0x2E, 'd': 0x20, 'e': 0x12, 'f': 0x21,
        'g': 0x22, 'h': 0x23, 'i': 0x17, 'j': 0x24, 'k': 0x25, 'l': 0x26,
        'm': 0x32, 'n': 0x31, 'o': 0x18, 'p': 0x19, 'q': 0x10, 'r': 0x13,
        's': 0x1F, 't': 0x14, 'u': 0x16, 'v': 0x2F, 'w': 0x11, 'x': 0x2D,
        'y': 0x15, 'z': 0x2C,
        '0': 0x0B, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05,
        '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A
    }

    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_KEYUP = 0x0002

    def __init__(self, humanize_level: float = 1.0):
        self.user32 = ctypes.windll.user32
        self.humanize_level = max(0.1, humanize_level)

    def _send_hardware_key(self, scancode: int, is_up: bool = False):
        """Émet un événement clavier Win32 via Scancode matériel DirectInput."""
        flags = self.KEYEVENTF_SCANCODE
        if is_up:
            flags |= self.KEYEVENTF_KEYUP
        try:
            self.user32.keybd_event(0, scancode, flags, 0)
        except Exception as e:
            print(f"[Le Scaphandre Keyboard] Erreur keybd_event: {e}")

    def send_key(self, key_name: str, hold_mean_sec: float = 0.055, hold_dev_sec: float = 0.015):
        """
        Enfonce et relâche une touche matérielle avec un temps de maintien distribué selon une Gaussienne.
        """
        key_lower = key_name.lower()
        scancode = self.SCANCODES.get(key_lower)
        
        # Scancode fallback via VkKeyScanW si non présent dans le dictionnaire
        if scancode is None:
            if len(key_name) == 1:
                vk = self.user32.VkKeyScanW(ord(key_name)) & 0xFF
                scancode = self.user32.MapVirtualKeyW(vk, 0)
            else:
                scancode = 0x1C  # Par défaut Entrée

        # Pression de la touche (KeyDown)
        self._send_hardware_key(scancode, is_up=False)

        # Temps de maintien réaliste (Gaussian Hold Time: moyenne ~55ms)
        hold_time = max(0.02, random.gauss(hold_mean_sec, hold_dev_sec)) / self.humanize_level
        time.sleep(hold_time)

        # Relâchement de la touche (KeyUp)
        self._send_hardware_key(scancode, is_up=True)

    def type_text(self, text: str, interkey_mean_sec: float = 0.075, interkey_dev_sec: float = 0.025):
        """
        Tape une chaîne de caractères caractère par caractère avec cadence variable humanisée.
        """
        for char in text:
            self.send_key(char)
            # Délai inter-touches Gaussien (rythme humain ~75ms/frappe)
            delay = max(0.03, random.gauss(interkey_mean_sec, interkey_dev_sec)) / self.humanize_level
            time.sleep(delay)

    def send_chat_message(self, message: str):
        """
        Ouvre le chat du jeu (Entrée), saisit le message de manière humanisée et valide (Entrée).
        """
        # 1. Ouvrir le chat
        self.send_key('enter')
        time.sleep(random.uniform(0.12, 0.25))

        # 2. Taper le texte
        self.type_text(message)
        time.sleep(random.uniform(0.08, 0.18))

        # 3. Valider
        self.send_key('enter')
        time.sleep(0.05)

if __name__ == "__main__":
    kbd = KeyboardSimulator()
    print("[Le Scaphandre] Simulateur clavier DirectInput initialisé.")
