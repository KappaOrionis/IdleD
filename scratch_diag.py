import ctypes
from ctypes import wintypes
import sys
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetDesktopWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL

def test_diagnostics():
    fg = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(fg, buf, 512)
    print(f"[Diag] GetForegroundWindow HWND: {fg}, Title: '{buf.value}'")

    print("\n[Diag] Windows list:")
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            b = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, b, 512)
            if b.value:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 50 and h > 50:
                    print(f"  - HWND {hwnd}: '{b.value}' ({w}x{h})")
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    print("\n[Diag] Testing Screen Grab:")
    try:
        im = ImageGrab.grab(all_screens=True)
        print(f"  - PIL ImageGrab OK: screen size is {im.size}")
    except Exception as e:
        print(f"  - PIL ImageGrab ERROR: {e}")

if __name__ == "__main__":
    test_diagnostics()
