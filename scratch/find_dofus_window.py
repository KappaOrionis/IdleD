import ctypes

user32 = ctypes.windll.user32
windows = []

def enum_windows_callback(hwnd, extra):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if any(k in title.lower() for k in ['dofus', 'ankama', 'unity', 'sufokia', 'amakna']):
                windows.append((hwnd, title))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

print('=== FENÊTRES JEU DÉTECTÉES ===')
for h, t in windows:
    print(f'HWND: {h} | Titre: "{t}"')
if not windows:
    print('Aucune fenêtre avec titre contenant dofus/ankama/unity trouvée. Recherche de tous les processus visibles...')
    all_vis = []
    def enum_all(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                all_vis.append((hwnd, buffer.value))
        return True
    user32.EnumWindows(WNDENUMPROC(enum_all), 0)
    for h, t in all_vis:
        if any(w in t.lower() for w in ['game', 'dofus', 'ankama', 'unity', 'launcher', 'chrome', 'edge']):
            print(f'  [Process Visible] HWND: {h} | Titre: "{t}"')
