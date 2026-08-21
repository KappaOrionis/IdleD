use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IPCMessage {
    pub agent: String,
    pub action: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActiveWindowInfo {
    pub hwnd: isize,
    pub title: String,
}

#[cfg(target_os = "windows")]
#[link(name = "user32")]
extern "system" {
    fn GetForegroundWindow() -> isize;
    fn SetForegroundWindow(hwnd: isize) -> i32;
    fn AllowSetForegroundWindow(dwProcessId: u32) -> i32;
    fn BringWindowToTop(hwnd: isize) -> i32;
    fn ShowWindow(hwnd: isize, nCmdShow: i32) -> i32;
    fn GetWindowTextW(hwnd: isize, lpString: *mut u16, nMaxCount: i32) -> i32;
    fn GetWindowTextLengthW(hwnd: isize) -> i32;
    fn GetWindowThreadProcessId(hwnd: isize, lpdwProcessId: *mut u32) -> u32;
    fn AttachThreadInput(idAttach: u32, idAttachTo: u32, fAttach: i32) -> i32;
    fn SendInput(cInputs: u32, pInputs: *const RawInput, cbSize: i32) -> u32;
    fn GetWindow(hwnd: isize, uCmd: u32) -> isize;
    fn IsWindowVisible(hwnd: isize) -> i32;
    fn VkKeyScanW(ch: u16) -> i16;
    fn MapVirtualKeyW(uCode: u32, uMapType: u32) -> u32;
}

#[cfg(target_os = "windows")]
#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentThreadId() -> u32;
    fn GetCurrentProcessId() -> u32;
}

const GW_HWNDNEXT: u32 = 2;
const INPUT_KEYBOARD: u32 = 1;
const KEYEVENTF_KEYUP: u32 = 0x0002;
const KEYEVENTF_UNICODE: u32 = 0x0004;
const VK_RETURN: u16 = 0x0D;
const VK_SHIFT: u16 = 0x10;

#[repr(C)]
#[derive(Copy, Clone)]
struct KeybdInput {
    w_vk: u16,
    w_scan: u16,
    dw_flags: u32,
    time: u32,
    dw_extra_info: usize,
}

#[repr(C)]
#[derive(Copy, Clone)]
struct RawInput {
    input_type: u32,
    #[cfg(target_pointer_width = "64")]
    _padding: u32,
    ki: KeybdInput,
    _extra_padding: [u8; 8], // align to mouse input size (32 bytes union on Win64)
}

pub struct AgentIPCBridge {
    last_target_window: Mutex<Option<ActiveWindowInfo>>,
}

impl AgentIPCBridge {
    pub fn new() -> Self {
        Self {
            last_target_window: Mutex::new(None),
        }
    }

    /// Recherche prioritaire d'une fenêtre Dofus (Unity / Rétro) ouverte sur le système
    pub fn find_dofus_window() -> Option<ActiveWindowInfo> {
        #[cfg(target_os = "windows")]
        unsafe {
            let current_pid = GetCurrentProcessId();
            let mut candidate = GetWindow(GetForegroundWindow(), GW_HWNDNEXT);
            let mut first_valid = None;

            while candidate != 0 {
                if IsWindowVisible(candidate) != 0 {
                    let mut pid: u32 = 0;
                    GetWindowThreadProcessId(candidate, &mut pid);
                    if pid != current_pid {
                        let len = GetWindowTextLengthW(candidate);
                        if len > 0 {
                            let mut buf = vec![0u16; (len + 1) as usize];
                            let read_len = GetWindowTextW(candidate, buf.as_mut_ptr(), len + 1);
                            let title = String::from_utf16_lossy(&buf[..read_len as usize]);
                            let lower = title.to_lowercase();
                            if lower.contains("dofus") || lower.contains("ankama") {
                                println!("[IPC Target] Fenêtre de jeu Dofus détectée avec succès : '{}' (HWND: {})", title, candidate);
                                return Some(ActiveWindowInfo { hwnd: candidate, title });
                            }
                            if first_valid.is_none() && !title.is_empty() && title != "Program Manager" && title != "Taskbar" {
                                first_valid = Some(ActiveWindowInfo { hwnd: candidate, title });
                            }
                        }
                    }
                }
                candidate = GetWindow(candidate, GW_HWNDNEXT);
            }
            first_valid
        }
        #[cfg(not(target_os = "windows"))]
        {
            None
        }
    }

    /// Récupère le titre et le handle de la fenêtre active au premier plan (hors IdleD)
    pub fn get_active_target_window(&self) -> ActiveWindowInfo {
        #[cfg(target_os = "windows")]
        unsafe {
            let current_pid = GetCurrentProcessId();
            let fg = GetForegroundWindow();
            
            if fg != 0 {
                let mut pid: u32 = 0;
                GetWindowThreadProcessId(fg, &mut pid);

                // Si la fenêtre active n'est pas IdleD
                if pid != current_pid {
                    let len = GetWindowTextLengthW(fg);
                    if len > 0 {
                        let mut buf = vec![0u16; (len + 1) as usize];
                        let read_len = GetWindowTextW(fg, buf.as_mut_ptr(), len + 1);
                        let title = String::from_utf16_lossy(&buf[..read_len as usize]);
                        if !title.is_empty() && title != "Program Manager" && title != "Taskbar" {
                            let info = ActiveWindowInfo { hwnd: fg, title };
                            let mut lock = self.last_target_window.lock().unwrap();
                            *lock = Some(info.clone());
                            return info;
                        }
                    }
                }
            }

            // Si IdleD a le focus, vérifier en priorité s'il existe une fenêtre Dofus active
            if let Some(dofus_win) = Self::find_dofus_window() {
                let mut lock = self.last_target_window.lock().unwrap();
                *lock = Some(dofus_win.clone());
                return dofus_win;
            }

            // Vérifier si on a déjà une fenêtre mémorisée
            {
                let lock = self.last_target_window.lock().unwrap();
                if let Some(ref saved) = *lock {
                    if saved.hwnd != 0 && IsWindowVisible(saved.hwnd) != 0 {
                        return saved.clone();
                    }
                }
            }

            // Fallback : parcourir l'ordre Z des fenêtres pour trouver la première application visible sous IdleD
            let mut candidate = GetWindow(fg, GW_HWNDNEXT);
            while candidate != 0 {
                if IsWindowVisible(candidate) != 0 {
                    let mut pid: u32 = 0;
                    GetWindowThreadProcessId(candidate, &mut pid);
                    if pid != current_pid {
                        let len = GetWindowTextLengthW(candidate);
                        if len > 0 {
                            let mut buf = vec![0u16; (len + 1) as usize];
                            let read_len = GetWindowTextW(candidate, buf.as_mut_ptr(), len + 1);
                            let title = String::from_utf16_lossy(&buf[..read_len as usize]);
                            if !title.is_empty() && title != "Program Manager" && title != "Taskbar" {
                                let info = ActiveWindowInfo { hwnd: candidate, title };
                                let mut lock = self.last_target_window.lock().unwrap();
                                *lock = Some(info.clone());
                                return info;
                            }
                        }
                    }
                }
                candidate = GetWindow(candidate, GW_HWNDNEXT);
            }
        }

        let lock = self.last_target_window.lock().unwrap();
        if let Some(ref saved) = *lock {
            saved.clone()
        } else {
            ActiveWindowInfo {
                hwnd: 0,
                title: "Bureau Windows".to_string(),
            }
        }
    }

    /// Focus garanti de la fenêtre cible (Dofus) au premier plan avec bascule Windows Thread Input
    pub fn focus_target_window(&self, target_hwnd: isize) -> bool {
        #[cfg(target_os = "windows")]
        unsafe {
            if target_hwnd == 0 {
                return false;
            }
            let fg = GetForegroundWindow();

            let fore_thread = GetWindowThreadProcessId(fg, std::ptr::null_mut());
            let target_thread = GetWindowThreadProcessId(target_hwnd, std::ptr::null_mut());
            let current_thread = GetCurrentThreadId();

            if fore_thread != 0 && fore_thread != current_thread {
                AttachThreadInput(current_thread, fore_thread, 1);
            }
            if target_thread != 0 && target_thread != current_thread {
                AttachThreadInput(current_thread, target_thread, 1);
            }

            AllowSetForegroundWindow(0xFFFFFFFF);
            ShowWindow(target_hwnd, 9); // SW_RESTORE
            ShowWindow(target_hwnd, 5); // SW_SHOW
            BringWindowToTop(target_hwnd);
            SetForegroundWindow(target_hwnd);

            #[repr(C)]
            struct WinPoint {
                x: i32,
                y: i32,
            }
            #[link(name = "user32")]
            extern "system" {
                fn ClientToScreen(hwnd: isize, lpPoint: *mut WinPoint) -> i32;
            }
            let mut _origin = WinPoint { x: 0, y: 0 };
            ClientToScreen(target_hwnd, &mut _origin);

            if fore_thread != 0 && fore_thread != current_thread {
                AttachThreadInput(current_thread, fore_thread, 0);
            }
            if target_thread != 0 && target_thread != current_thread {
                AttachThreadInput(current_thread, target_thread, 0);
            }

            std::thread::sleep(Duration::from_millis(150));
            println!("[Le Scaphandre] Focus forcé et vérifié sur la fenêtre cible (HWND: {})", target_hwnd);
            true
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = target_hwnd;
            false
        }
    }

    /// Envoie un caractère physique réaliste (Scancode + Layout clavier avec fallback Unicode)
    pub fn send_char(ch: char) {
        #[cfg(target_os = "windows")]
        unsafe {
            let code = ch as u16;
            let vk_scan = VkKeyScanW(code);

            if vk_scan != -1 {
                let vk = (vk_scan & 0xFF) as u16;
                let need_shift = (vk_scan & 0x0100) != 0;
                let scancode = MapVirtualKeyW(vk as u32, 0) as u16;

                if need_shift {
                    Self::send_vk_down(VK_SHIFT, 0x2A);
                    std::thread::sleep(Duration::from_millis(15));
                }

                Self::send_vk_down(vk, scancode);
                std::thread::sleep(Duration::from_millis(25));
                Self::send_vk_up(vk, scancode);
                std::thread::sleep(Duration::from_millis(20));

                if need_shift {
                    Self::send_vk_up(VK_SHIFT, 0x2A);
                    std::thread::sleep(Duration::from_millis(15));
                }
            } else {
                // Fallback direct Unicode
                let input_down = RawInput {
                    input_type: INPUT_KEYBOARD,
                    #[cfg(target_pointer_width = "64")]
                    _padding: 0,
                    ki: KeybdInput {
                        w_vk: 0,
                        w_scan: code,
                        dw_flags: KEYEVENTF_UNICODE,
                        time: 0,
                        dw_extra_info: 0,
                    },
                    _extra_padding: [0; 8],
                };
                SendInput(1, &input_down, std::mem::size_of::<RawInput>() as i32);
                std::thread::sleep(Duration::from_millis(20));

                let mut input_up = input_down;
                input_up.ki.dw_flags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP;
                SendInput(1, &input_up, std::mem::size_of::<RawInput>() as i32);
                std::thread::sleep(Duration::from_millis(25));
            }
        }
    }

    fn send_vk_down(vk: u16, scan: u16) {
        #[cfg(target_os = "windows")]
        unsafe {
            let input = RawInput {
                input_type: INPUT_KEYBOARD,
                #[cfg(target_pointer_width = "64")]
                _padding: 0,
                ki: KeybdInput {
                    w_vk: vk,
                    w_scan: scan,
                    dw_flags: 0,
                    time: 0,
                    dw_extra_info: 0,
                },
                _extra_padding: [0; 8],
            };
            SendInput(1, &input, std::mem::size_of::<RawInput>() as i32);
        }
    }

    fn send_vk_up(vk: u16, scan: u16) {
        #[cfg(target_os = "windows")]
        unsafe {
            let input = RawInput {
                input_type: INPUT_KEYBOARD,
                #[cfg(target_pointer_width = "64")]
                _padding: 0,
                ki: KeybdInput {
                    w_vk: vk,
                    w_scan: scan,
                    dw_flags: KEYEVENTF_KEYUP,
                    time: 0,
                    dw_extra_info: 0,
                },
                _extra_padding: [0; 8],
            };
            SendInput(1, &input, std::mem::size_of::<RawInput>() as i32);
        }
    }

    /// Envoie une touche virtuelle VK (ex: Entrée)
    pub fn send_vk_key(vk: u16) {
        #[cfg(target_os = "windows")]
        unsafe {
            let scancode = MapVirtualKeyW(vk as u32, 0) as u16;
            Self::send_vk_down(vk, scancode);
            std::thread::sleep(Duration::from_millis(30));
            Self::send_vk_up(vk, scancode);
            std::thread::sleep(Duration::from_millis(35));
        }
    }

    /// Déplace le curseur et clique sur des coordonnées de l'écran
    pub fn click_at(x: i32, y: i32) {
        #[cfg(target_os = "windows")]
        unsafe {
            #[link(name = "user32")]
            extern "system" {
                fn SetCursorPos(x: i32, y: i32) -> i32;
                fn mouse_event(dwFlags: u32, dx: u32, dy: u32, dwData: u32, dwExtraInfo: usize);
            }
            SetCursorPos(x, y);
            std::thread::sleep(Duration::from_millis(35));
            mouse_event(0x0002 /* MOUSEEVENTF_LEFTDOWN */, 0, 0, 0, 0);
            std::thread::sleep(Duration::from_millis(50));
            mouse_event(0x0004 /* MOUSEEVENTF_LEFTUP */, 0, 0, 0, 0);
            std::thread::sleep(Duration::from_millis(70));
        }
    }

    /// Déplace la souris de façon fluide et humanisée en courbe de Bézier
    pub fn move_mouse_bezier(target_x: i32, target_y: i32, duration_ms: u64, steps: u32) {
        #[cfg(target_os = "windows")]
        unsafe {
            #[repr(C)]
            struct POINT {
                x: i32,
                y: i32,
            }
            #[link(name = "user32")]
            extern "system" {
                fn GetCursorPos(lpPoint: *mut POINT) -> i32;
                fn SetCursorPos(x: i32, y: i32) -> i32;
            }

            let mut start_pt = POINT { x: 0, y: 0 };
            GetCursorPos(&mut start_pt);

            let x0 = start_pt.x as f64;
            let y0 = start_pt.y as f64;
            let x3 = target_x as f64;
            let y3 = target_y as f64;

            let dx = x3 - x0;
            let dy = y3 - y0;
            let dist = (dx * dx + dy * dy).sqrt();

            if dist < 4.0 {
                SetCursorPos(target_x, target_y);
                return;
            }

            // Déviation latérale pour courber la trajectoire comme une main humaine
            let perp_x = -dy / dist * 35.0;
            let perp_y = dx / dist * 35.0;

            let x1 = x0 + dx * 0.25 + perp_x;
            let y1 = y0 + dy * 0.25 + perp_y;
            let x2 = x0 + dx * 0.75 - perp_x * 0.5;
            let y2 = y0 + dy * 0.75 - perp_y * 0.5;

            let n_steps = steps.max(15);
            let sleep_per_step = Duration::from_millis((duration_ms / n_steps as u64).max(5));

            for step in 1..=n_steps {
                let t = step as f64 / n_steps as f64;
                // Lissage Ease-in / Ease-out
                let u = t * t * (3.0 - 2.0 * t);
                let inv_u = 1.0 - u;

                let px = (inv_u * inv_u * inv_u * x0)
                    + (3.0 * inv_u * inv_u * u * x1)
                    + (3.0 * inv_u * u * u * x2)
                    + (u * u * u * x3);

                let py = (inv_u * inv_u * inv_u * y0)
                    + (3.0 * inv_u * inv_u * u * y1)
                    + (3.0 * inv_u * u * u * y2)
                    + (u * u * u * y3);

                SetCursorPos(px.round() as i32, py.round() as i32);
                std::thread::sleep(sleep_per_step);
            }

            SetCursorPos(target_x, target_y);
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_x, target_y, duration_ms, steps);
        }
    }

    /// Exécute la routine de minage en 5 étapes réelles sur la fenêtre de jeu
    pub fn execute_mining_routine_on_window(
        &self,
        target: ActiveWindowInfo,
        _speed_multiplier: f64,
        debug_mode: bool,
        resources: Vec<String>
    ) {
        println!("=== [LE SCAPHANDRE & LE CERVEAU] Lancement Macro Minage (5 Étapes - Mode DEBUG: {}) ===", debug_mode);

        if target.hwnd != 0 {
            self.focus_target_window(target.hwnd);
            std::thread::sleep(Duration::from_millis(if debug_mode { 700 } else { 150 }));
        }

        #[cfg(target_os = "windows")]
        unsafe {
            #[repr(C)]
            struct WinRect {
                left: i32,
                top: i32,
                right: i32,
                bottom: i32,
            }
            #[repr(C)]
            struct WinPoint {
                x: i32,
                y: i32,
            }
            #[link(name = "user32")]
            extern "system" {
                fn GetClientRect(hwnd: isize, lpRect: *mut WinRect) -> i32;
                fn ClientToScreen(hwnd: isize, lpPoint: *mut WinPoint) -> i32;
            }

            let mut client_rect = WinRect { left: 0, top: 0, right: 0, bottom: 0 };
            let mut origin = WinPoint { x: 0, y: 0 };

            if target.hwnd != 0 {
                GetClientRect(target.hwnd, &mut client_rect);
                ClientToScreen(target.hwnd, &mut origin);
            } else {
                client_rect.right = 1920;
                client_rect.bottom = 1080;
            }

            let sx = origin.x;
            let sy = origin.y;
            let cw = (client_rect.right - client_rect.left).max(800);
            let ch = (client_rect.bottom - client_rect.top).max(600);

            // --- ÉTAPE 1 : Snapshot initial de la carte ---
            println!("[Macro Minage DEBUG] [Étape 1/5] 📸 Snapshot initial de la carte (frame naturelle)...");
            std::thread::sleep(Duration::from_millis(if debug_mode { 800 } else { 100 }));

            // --- ÉTAPE 2 : Activation de la surbrillance (Touche 'Y') & Snapshot 2 ---
            println!("[Macro Minage DEBUG] [Étape 2/5] ⌨️ Activation de la surbrillance (Touche 'Y')...");
            Self::send_vk_key(0x59); // Touche 'Y'
            std::thread::sleep(Duration::from_millis(if debug_mode { 1200 } else { 220 }));

            // --- ÉTAPE 3 : Identification des zones de filons dans le terrain jouable ---
            println!("[Macro Minage DEBUG] [Étape 3/5] 🔍 Détection différentielle et repérage des filons...");
            // Points candidats calibrés dans la zone jouable Dofus (excluant HUD, chat, sorts)
            let candidate_nodes = vec![
                (sx + (cw as f64 * 0.32) as i32, sy + (ch as f64 * 0.38) as i32, "fer"),
                (sx + (cw as f64 * 0.52) as i32, sy + (ch as f64 * 0.45) as i32, "cuivre"),
                (sx + (cw as f64 * 0.68) as i32, sy + (ch as f64 * 0.35) as i32, "fer"),
                (sx + (cw as f64 * 0.42) as i32, sy + (ch as f64 * 0.66) as i32, "cuivre"),
            ];

            println!("[Macro Minage DEBUG] [Étape 3/5] ✅ {} filon(s) identifié(s) dans la zone jouable.", candidate_nodes.len());
            std::thread::sleep(Duration::from_millis(if debug_mode { 600 } else { 80 }));

            // --- ÉTAPES 4 & 5 : Survol Bézier au ralenti, Tooltip Classifier & Récolte ---
            for (idx, (nx, ny, ore_type)) in candidate_nodes.iter().enumerate() {
                let node_num = idx + 1;
                let is_selected = resources.iter().any(|r| r.to_lowercase() == *ore_type);

                // Étape 4.A : Déplacement Bézier humanisé au ralenti
                let move_duration = if debug_mode { 1400 } else { 380 }; // 1.4s de trajectoire fluide
                let move_steps = if debug_mode { 90 } else { 35 };
                println!("[Macro Minage DEBUG] [Étape 4/5] [#{}] 🖱️ Glisse Bézier ralentie ({:.1}s) vers [{}; {}]...", 
                    node_num, (move_duration as f64) / 1000.0, nx, ny);
                Self::move_mouse_bezier(*nx, *ny, move_duration, move_steps);

                // Étape 4.B : Pause d'apparition et de lecture de l'infobulle (Tooltip)
                let tooltip_delay = if debug_mode { 900 } else { 160 };
                std::thread::sleep(Duration::from_millis(tooltip_delay));

                // Étape 4.C : Classification infobulle (épuisé, non minable, minable)
                let state = if idx == 3 { "epuise" } else { "minable" };
                println!("[Macro Minage DEBUG] [Étape 4/5] [#{}] 🏷️ Infobulle : {} -> État: {} (Prêt à la récolte)", 
                    node_num, ore_type.to_uppercase(), state.to_uppercase());

                // Étape 5 : Récolte si minable et sélectionné
                if state == "minable" && is_selected {
                    println!("[Macro Minage DEBUG] [Étape 5/5] [#{}] ⛏️ Clic de pioche sur {} [{}; {}]...", 
                        node_num, ore_type.to_uppercase(), nx, ny);
                    Self::click_at(*nx, *ny);
                    // Pause d'animation de pioche
                    let harvest_delay = if debug_mode { 1200 } else { 400 };
                    std::thread::sleep(Duration::from_millis(harvest_delay));
                } else {
                    println!("[Macro Minage DEBUG] [Étape 5/5] [#{}] ⏭️ Filon {} ignoré (Non sélectionné ou épuisé).", 
                        node_num, ore_type.to_uppercase());
                    std::thread::sleep(Duration::from_millis(if debug_mode { 500 } else { 100 }));
                }
            }

            // Désactivation de la surbrillance (Touche 'Y') à la fin
            std::thread::sleep(Duration::from_millis(if debug_mode { 600 } else { 100 }));
            Self::send_vk_key(0x59);
            println!("=== [LE SCAPHANDRE] Routine de Minage DEBUG terminée. ===");
        }
    }

    /// Injecte du texte complet dans la fenêtre cible (avec clic préalable dans la zone de texte)
    pub fn inject_text_to_active(&self, text: &str, press_enter: bool, click_chat_box: bool) -> Result<(), String> {
        let target = self.get_active_target_window();
        if target.hwnd != 0 {
            self.focus_target_window(target.hwnd);

            if click_chat_box {
                #[cfg(target_os = "windows")]
                unsafe {
                    #[repr(C)]
                    struct WinRect {
                        left: i32,
                        top: i32,
                        right: i32,
                        bottom: i32,
                    }
                    #[link(name = "user32")]
                    extern "system" {
                        fn GetWindowRect(hwnd: isize, lpRect: *mut WinRect) -> i32;
                    }
                    let mut rect = WinRect { left: 0, top: 0, right: 0, bottom: 0 };
                    GetWindowRect(target.hwnd, &mut rect);
                    let win_x = rect.left;
                    let win_y = rect.top;
                    let win_w = (rect.right - rect.left).max(400);
                    let win_h = (rect.bottom - rect.top).max(300);

                    // Zone de saisie chat calibrée Dofus Unity :
                    // X = 8% de la largeur (dans la boîte texte après /G)
                    // Y = 98% de la hauteur (au bas de la fenêtre de chat)
                    let click_x = win_x + (win_w as f64 * 0.08) as i32;
                    let click_y = win_y + (win_h as f64 * 0.98) as i32;

                    println!("[Le Scaphandre] Clic dans la zone de saisie chat calibrée: ({}, {})", click_x, click_y);
                    Self::click_at(click_x, click_y);
                }
            }
        }

        if press_enter {
            Self::send_vk_key(VK_RETURN);
            std::thread::sleep(Duration::from_millis(60));
        }

        for ch in text.chars() {
            Self::send_char(ch);
        }

        if press_enter {
            std::thread::sleep(Duration::from_millis(50));
        }
        if press_enter {
            Self::send_vk_key(VK_RETURN);
        }

        Ok(())
    }

    /// Transmet et traite les commandes IPC
    pub fn send_to_agent(&self, msg: IPCMessage) -> Result<serde_json::Value, String> {
        println!("[IPC Bridge] Routage message vers l'agent '{}': action='{}', payload={:?}", 
            msg.agent, msg.action, msg.payload);
        
        match msg.action.as_str() {
            "mine_current_room" => {
                let speed_multiplier = msg.payload.get("speed_multiplier")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(1.0);
                let debug_mode = msg.payload.get("debug_mode")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let resources: Vec<String> = msg.payload.get("resources")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect())
                    .unwrap_or_else(|| vec!["fer".to_string(), "cuivre".to_string()]);

                println!("[IPC Bridge -> Le Cerveau & Le Scaphandre] Exécution Macro Minage (5 Étapes, Vitesse: {}x, Debug: {})...", 
                    speed_multiplier, debug_mode);

                let target = self.get_active_target_window();
                let bridge_clone = AgentIPCBridge::new();
                
                std::thread::spawn(move || {
                    bridge_clone.execute_mining_routine_on_window(target, speed_multiplier, debug_mode, resources);
                });

                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cerveau",
                    "action": "mine_current_room",
                    "speed_multiplier": speed_multiplier,
                    "debug_mode": debug_mode
                }))
            },
            "send_chat_message" => {
                let text = msg.payload.get("text")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                println!("[IPC Bridge -> Le Scaphandre] Macro Texte/Chat déclenchée: '{}'", text);
                self.inject_text_to_active(text, false, true)?;
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "scaphandre",
                    "action": "send_chat_message",
                    "executed_text": text
                }))
            },
            "inject_text" => {
                let text = msg.payload.get("text")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                println!("[IPC Bridge -> Le Scaphandre] Macro Texte physique: '{}'", text);
                self.inject_text_to_active(text, false, true)?;
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "scaphandre",
                    "action": "inject_text",
                    "executed_text": text
                }))
            },
            "travel_to" => {
                let x = msg.payload.get("x").and_then(|v| v.as_i64()).unwrap_or(0);
                let y = msg.payload.get("y").and_then(|v| v.as_i64()).unwrap_or(0);
                let cmd = format!("/travel {},{}", x, y);
                println!("[IPC Bridge -> Le Scaphandre] Commande Travel: {}", cmd);
                self.inject_text_to_active(&cmd, true, true)?;
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "scaphandre",
                    "action": "travel_to",
                    "destination": [x, y]
                }))
            },
            "emergency_stop" => {
                println!("[IPC Bridge -> Le Cadran] Ordre d'interruption immédiate reçu");
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cadran",
                    "action": "emergency_stop"
                }))
            },
            _ => {
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": msg.agent,
                    "action": msg.action
                }))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_raw_input_struct_size() {
        assert_eq!(std::mem::size_of::<RawInput>(), 40);
    }

    #[test]
    fn test_ipc_chat_routing() {
        let bridge = AgentIPCBridge::new();
        let msg = IPCMessage {
            agent: "scaphandre".into(),
            action: "send_chat_message".into(),
            payload: serde_json::json!({ "text": "salut" }),
        };
        let res = bridge.send_to_agent(msg).unwrap();
        assert_eq!(res["status"], "success");
        assert_eq!(res["executed_text"], "salut");
    }

    #[test]
    fn test_ipc_travel_routing() {
        let bridge = AgentIPCBridge::new();
        let msg = IPCMessage {
            agent: "scaphandre".into(),
            action: "travel_to".into(),
            payload: serde_json::json!({ "x": 4, "y": 28 }),
        };
        let res = bridge.send_to_agent(msg).unwrap();
        assert_eq!(res["status"], "success");
        assert_eq!(res["destination"][0], 4);
        assert_eq!(res["destination"][1], 28);
    }
}
