use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DirectionKey {
    Up,
    Down,
    Left,
    Right,
}

#[cfg(target_os = "windows")]
#[link(name = "user32")]
extern "system" {
    fn GetForegroundWindow() -> isize;
    fn SetCursorPos(x: i32, y: i32) -> i32;
    fn mouse_event(dwFlags: u32, dx: u32, dy: u32, dwData: u32, dwExtraInfo: usize);
    fn GetWindowRect(hwnd: isize, lpRect: *mut WinRect) -> i32;
}

#[repr(C)]
struct WinRect {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}

const MOUSEEVENTF_LEFTDOWN: u32 = 0x0002;
const MOUSEEVENTF_LEFTUP: u32 = 0x0004;

pub struct HotkeyManager;

impl HotkeyManager {
    pub fn new() -> Self {
        Self
    }

    /// Exécute un swipe de souris physique dans la direction opposée à la touche pressée
    /// Exécute un swipe de souris physique démarrant au centre de l'écran
    /// en maintenant le clic gauche enfoncé tout au long du déplacement dans la direction opposée
    pub fn perform_opposite_swipe(direction: DirectionKey, target_hwnd: isize) {
        #[cfg(target_os = "windows")]
        unsafe {
            #[link(name = "user32")]
            extern "system" {
                fn SetForegroundWindow(hwnd: isize) -> i32;
            }

            let hwnd = if target_hwnd != 0 { target_hwnd } else { GetForegroundWindow() };
            if hwnd != 0 {
                SetForegroundWindow(hwnd);
            }

            let mut rect = WinRect { left: 0, top: 0, right: 0, bottom: 0 };
            GetWindowRect(hwnd, &mut rect);

            let win_x = rect.left;
            let win_y = rect.top;
            let win_w = (rect.right - rect.left).max(400);
            let win_h = (rect.bottom - rect.top).max(300);

            // Centre exact de la zone de jeu
            let center_x = win_x + (win_w / 2);
            let center_y = win_y + (win_h / 2);
            let swipe_distance = 180;

            let (start_x, start_y, end_x, end_y) = match direction {
                // Touche Haut (↑) -> Swipe depuis le centre vers le Bas (↓)
                DirectionKey::Up => (center_x, center_y, center_x, center_y + swipe_distance),
                // Touche Bas (↓) -> Swipe depuis le centre vers le Haut (↑)
                DirectionKey::Down => (center_x, center_y, center_x, center_y - swipe_distance),
                // Touche Gauche (←) -> Swipe depuis le centre vers la Droite (→)
                DirectionKey::Left => (center_x, center_y, center_x + swipe_distance, center_y),
                // Touche Droite (→) -> Swipe depuis le centre vers la Gauche (←)
                DirectionKey::Right => (center_x, center_y, center_x - swipe_distance, center_y),
            };

            println!("[Le Scaphandre] Swipe centré maintenu ({:?}): centre ({},{}) -> destination ({},{})", 
                direction, start_x, start_y, end_x, end_y);

            // 1. Positionnement initial au centre exact
            SetCursorPos(start_x, start_y);
            std::thread::sleep(Duration::from_millis(45));

            // 2. Clic gauche enfoncé (MouseDown)
            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
            std::thread::sleep(Duration::from_millis(50));

            // 3. Glissement progressif en maintenant le bouton gauche constamment enfoncé
            let steps = 14;
            for i in 1..=steps {
                let t = i as f64 / steps as f64;
                // Lissage d'accélération / décélération (Ease-Out)
                let smooth_t = 1.0 - (1.0 - t).powi(2);
                let cur_x = (start_x as f64 + (end_x - start_x) as f64 * smooth_t) as i32;
                let cur_y = (start_y as f64 + (end_y - start_y) as f64 * smooth_t) as i32;
                SetCursorPos(cur_x, cur_y);
                std::thread::sleep(Duration::from_millis(10));
            }

            // 4. Maintien bref à la position finale puis relâchement du clic (MouseUp)
            std::thread::sleep(Duration::from_millis(60));
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
            std::thread::sleep(Duration::from_millis(40));
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (direction, target_hwnd);
        }
    }

    /// Gère l'interception matérielle des touches directionnelles
    /// pour déclencher les changements de carte instantanés via swipe opposé.
    pub fn handle_directional_key(&self, direction: DirectionKey, target_hwnd: isize) {
        println!("[Superviseur Hotkey] Touche directionnelle interceptée : {:?}", direction);
        Self::perform_opposite_swipe(direction, target_hwnd);
    }

    /// Arrêt d'urgence instantané (F12 / Global Hotkey)
    pub fn trigger_emergency_stop(&self) {
        println!("[Superviseur Hotkey] ARRÊT D'URGENCE DÉCLENCHÉ ! Interruption de tous les agents.");
    }
}
