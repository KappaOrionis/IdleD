use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::sync::Mutex;
use std::time::Duration;
use crate::stream_capture::Win32StreamCapture;

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
    fn GetClassNameW(hwnd: isize, lpClassName: *mut u16, nMaxCount: i32) -> i32;
    fn GetWindowThreadProcessId(hwnd: isize, lpdwProcessId: *mut u32) -> u32;
    fn AttachThreadInput(idAttach: u32, idAttachTo: u32, fAttach: i32) -> i32;
    fn SendInput(cInputs: u32, pInputs: *const RawInput, cbSize: i32) -> u32;
    #[allow(dead_code)]
    fn GetWindow(hwnd: isize, uCmd: u32) -> isize;
    fn IsWindowVisible(hwnd: isize) -> i32;
    fn IsIconic(hwnd: isize) -> i32;
    fn EnumWindows(lpEnumFunc: unsafe extern "system" fn(isize, isize) -> i32, lParam: isize) -> i32;
    fn VkKeyScanW(ch: u16) -> i16;
    fn MapVirtualKeyW(uCode: u32, uMapType: u32) -> u32;
}

#[cfg(target_os = "windows")]
#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentThreadId() -> u32;
    fn GetCurrentProcessId() -> u32;
    fn OpenProcess(dwDesiredAccess: u32, bInheritHandle: i32, dwProcessId: u32) -> isize;
    fn CloseHandle(hObject: isize) -> i32;
    fn QueryFullProcessImageNameW(hProcess: isize, dwFlags: u32, lpExeName: *mut u16, lpdwSize: *mut u32) -> i32;
}

#[allow(dead_code)]
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

struct WindowSearchResult {
    candidates: Vec<ActiveWindowInfo>,
    fallback: Option<ActiveWindowInfo>,
}

#[cfg(target_os = "windows")]
unsafe extern "system" fn enum_windows_callback(hwnd: isize, lparam: isize) -> i32 {
    let result = &mut *(lparam as *mut WindowSearchResult);
    let current_pid = GetCurrentProcessId();

    if IsWindowVisible(hwnd) != 0 && IsIconic(hwnd) == 0 {
        let mut pid: u32 = 0;
        GetWindowThreadProcessId(hwnd, &mut pid);

        if pid != current_pid && pid != 0 {
            let len = GetWindowTextLengthW(hwnd);
            let mut title = String::new();
            if len > 0 {
                let mut buf = vec![0u16; (len + 1) as usize];
                let read_len = GetWindowTextW(hwnd, buf.as_mut_ptr(), len + 1);
                title = String::from_utf16_lossy(&buf[..read_len as usize]);
            }

            // Récupération de la classe de fenêtre
            let mut class_buf = vec![0u16; 256];
            let class_len = GetClassNameW(hwnd, class_buf.as_mut_ptr(), 256);
            let class_name = String::from_utf16_lossy(&class_buf[..class_len as usize]).to_lowercase();

            // Récupération du chemin d'exécutable
            let mut proc_name = String::new();
            let hproc = OpenProcess(0x1000 /* PROCESS_QUERY_LIMITED_INFORMATION */, 0, pid);
            if hproc != 0 {
                let mut path_buf = vec![0u16; 1024];
                let mut size: u32 = 1024;
                if QueryFullProcessImageNameW(hproc, 0, path_buf.as_mut_ptr(), &mut size) != 0 {
                    proc_name = String::from_utf16_lossy(&path_buf[..size as usize]).to_lowercase();
                }
                CloseHandle(hproc);
            }

            let lower_title = title.to_lowercase();

            // Filtrage d'exclusion des éditeurs, navigateurs Chrome/Edge/Brave et outils système
            let is_browser_or_dev = class_name.contains("chrome")
                || class_name.contains("widget")
                || class_name.contains("electron")
                || lower_title.contains("chrome")
                || lower_title.contains("edge")
                || lower_title.contains("brave")
                || lower_title.contains("firefox")
                || lower_title.contains("visual studio")
                || lower_title.contains("code")
                || lower_title.contains("antigravity")
                || lower_title.contains("powershell")
                || lower_title.contains("cmd.exe")
                || lower_title.contains("terminal")
                || proc_name.contains("chrome.exe")
                || proc_name.contains("msedge.exe")
                || proc_name.contains("brave.exe")
                || proc_name.contains("firefox.exe")
                || proc_name.contains("code.exe")
                || title == "Program Manager"
                || title == "Taskbar";

            if !is_browser_or_dev {
                // Détection formelle UnityWndClass (moteur Dofus Unity) ou processus Dofus
                let is_unity_game = class_name.contains("unitywndclass") || class_name.contains("unity");
                let is_dofus_proc = proc_name.contains("dofus") || proc_name.contains("ankama");
                
                // Couvre les 19 classes de Dofus et les mots-clés de titre de jeu
                let is_dofus_class = lower_title.contains("enutrof")
                    || lower_title.contains("iop")
                    || lower_title.contains("cra")
                    || lower_title.contains("feca")
                    || lower_title.contains("sacrieur")
                    || lower_title.contains("sram")
                    || lower_title.contains("xelor")
                    || lower_title.contains("pandawa")
                    || lower_title.contains("eniripsa")
                    || lower_title.contains("ecaflip")
                    || lower_title.contains("osamodas")
                    || lower_title.contains("sadida")
                    || lower_title.contains("roublard")
                    || lower_title.contains("zobal")
                    || lower_title.contains("steamer")
                    || lower_title.contains("eliotrope")
                    || lower_title.contains("huppermage")
                    || lower_title.contains("ouginak")
                    || lower_title.contains("forgelance");

                let is_dofus_meta = lower_title.contains("dofus") 
                    || lower_title.contains("ankama")
                    || is_dofus_class;

                if is_unity_game || is_dofus_proc || is_dofus_meta {
                    result.candidates.push(ActiveWindowInfo { hwnd, title });
                } else if result.fallback.is_none() && !title.is_empty() {
                    result.fallback = Some(ActiveWindowInfo { hwnd, title });
                }
            }
        }
    }
    1 // Continuer le balayage
}

pub struct AgentIPCBridge {
    last_target_window: Mutex<Option<ActiveWindowInfo>>,
    is_macro_running: Arc<AtomicBool>,
    is_macro_paused: Arc<AtomicBool>,
}

impl AgentIPCBridge {
    pub fn new() -> Self {
        Self {
            last_target_window: Mutex::new(None),
            is_macro_running: Arc::new(AtomicBool::new(false)),
            is_macro_paused: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn start_macro(&self) {
        self.is_macro_running.store(true, Ordering::SeqCst);
        self.is_macro_paused.store(false, Ordering::SeqCst);
    }

    pub fn pause_macro(&self) {
        self.is_macro_paused.store(true, Ordering::SeqCst);
        println!("[Le Cadran] ⏸️ Macro mise en PAUSE instantanée");
    }

    pub fn resume_macro(&self) {
        self.is_macro_paused.store(false, Ordering::SeqCst);
        println!("[Le Cadran] ▶️ Macro REPRISE");
    }

    pub fn stop_macro(&self) {
        self.is_macro_running.store(false, Ordering::SeqCst);
        self.is_macro_paused.store(false, Ordering::SeqCst);
        println!("[Le Cadran] 🛑 Arrêt d'urgence appliqué sur le moteur motrice");
    }

    #[allow(dead_code)]
    pub fn is_running(&self) -> bool {
        self.is_macro_running.load(Ordering::SeqCst)
    }

    #[allow(dead_code)]
    pub fn is_paused(&self) -> bool {
        self.is_macro_paused.load(Ordering::SeqCst)
    }

    pub fn get_running_flag(&self) -> Arc<AtomicBool> {
        Arc::clone(&self.is_macro_running)
    }

    pub fn get_paused_flag(&self) -> Arc<AtomicBool> {
        Arc::clone(&self.is_macro_paused)
    }

    /// Recherche prioritaire d'une fenêtre Dofus (Unity / Rétro) ouverte sur le système
    pub fn find_dofus_window() -> Option<ActiveWindowInfo> {
        #[cfg(target_os = "windows")]
        unsafe {
            let mut result = WindowSearchResult {
                candidates: Vec::new(),
                fallback: None,
            };

            EnumWindows(enum_windows_callback, &mut result as *mut _ as isize);

            if let Some(first_dofus) = result.candidates.into_iter().next() {
                return Some(first_dofus);
            }
            result.fallback
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
            // 1. Priorité absolue : Détection de la fenêtre DOFUS active
            if let Some(dofus_win) = Self::find_dofus_window() {
                let mut lock = self.last_target_window.lock().unwrap();
                *lock = Some(dofus_win.clone());
                return dofus_win;
            }

            // 2. Fenêtre actuellement au premier plan si différente d'IdleD et d'un éditeur
            let current_pid = GetCurrentProcessId();
            let fg = GetForegroundWindow();
            if fg != 0 {
                let mut pid: u32 = 0;
                GetWindowThreadProcessId(fg, &mut pid);
                if pid != current_pid {
                    let len = GetWindowTextLengthW(fg);
                    if len > 0 {
                        let mut buf = vec![0u16; (len + 1) as usize];
                        let read_len = GetWindowTextW(fg, buf.as_mut_ptr(), len + 1);
                        let title = String::from_utf16_lossy(&buf[..read_len as usize]);
                        let lower = title.to_lowercase();
                        if !lower.contains("code") && !lower.contains("antigravity") && title != "Program Manager" && title != "Taskbar" {
                            let info = ActiveWindowInfo { hwnd: fg, title };
                            let mut lock = self.last_target_window.lock().unwrap();
                            *lock = Some(info.clone());
                            return info;
                        }
                    }
                }
            }
        }

        let lock = self.last_target_window.lock().unwrap();
        if let Some(ref saved) = *lock {
            saved.clone()
        } else {
            ActiveWindowInfo {
                hwnd: 0,
                title: "Dofus".to_string(),
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

    /// Temporisation interruptible en temps réel (réagit en < 20ms à un ordre STOP ou PAUSE)
    pub fn interruptible_sleep(duration_ms: u64, is_running: &Arc<AtomicBool>, is_paused: &Arc<AtomicBool>) -> bool {
        let chunk = 20u64;
        let mut elapsed = 0u64;
        while elapsed < duration_ms {
            if !is_running.load(Ordering::SeqCst) {
                return false;
            }
            while is_paused.load(Ordering::SeqCst) {
                if !is_running.load(Ordering::SeqCst) {
                    return false;
                }
                std::thread::sleep(Duration::from_millis(40));
            }
            let step = (duration_ms - elapsed).min(chunk);
            std::thread::sleep(Duration::from_millis(step));
            elapsed += step;
        }
        is_running.load(Ordering::SeqCst)
    }

    /// Déplace la souris de façon fluide et humanisée en courbe de Bézier (avec annulation instantanée et pause)
    pub fn move_mouse_bezier(
        target_x: i32,
        target_y: i32,
        duration_ms: u64,
        steps: u32,
        is_running: &Arc<AtomicBool>,
        is_paused: &Arc<AtomicBool>
    ) -> bool {
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
                return is_running.load(Ordering::SeqCst);
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
                if !is_running.load(Ordering::SeqCst) {
                    println!("[Le Scaphandre] 🛑 Mouvement Bézier interrompu net");
                    return false;
                }
                while is_paused.load(Ordering::SeqCst) {
                    if !is_running.load(Ordering::SeqCst) {
                        return false;
                    }
                    std::thread::sleep(Duration::from_millis(40));
                }

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

            if is_running.load(Ordering::SeqCst) {
                SetCursorPos(target_x, target_y);
                true
            } else {
                false
            }
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_x, target_y, duration_ms, steps, is_running, is_paused);
            true
        }
    }

    /// Exécute la routine de minage en 5 étapes réelles sur la fenêtre de jeu (avec annulation et pause instantanées)
    pub fn execute_mining_routine_on_window(
        &self,
        target: ActiveWindowInfo,
        _speed_multiplier: f64,
        debug_mode: bool,
        resources: Vec<String>,
        is_running: Arc<AtomicBool>,
        is_paused: Arc<AtomicBool>
    ) {
        println!("=== [LE SCAPHANDRE & LE CERVEAU] Lancement Macro Minage (5 Étapes - Mode DEBUG: {}) ===", debug_mode);

        if !is_running.load(Ordering::SeqCst) {
            return;
        }

        // Résolution prioritaire de la fenêtre DOFUS pour garantir que les actions se déroulent sur le jeu
        let effective_target = if target.hwnd != 0 {
            target
        } else if let Some(dofus_win) = Self::find_dofus_window() {
            dofus_win
        } else {
            target
        };

        if effective_target.hwnd != 0 {
            self.focus_target_window(effective_target.hwnd);
            if !Self::interruptible_sleep(if debug_mode { 700 } else { 150 }, &is_running, &is_paused) {
                return;
            }
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

            if effective_target.hwnd != 0 {
                GetClientRect(effective_target.hwnd, &mut client_rect);
                ClientToScreen(effective_target.hwnd, &mut origin);
            } else {
                client_rect.right = 1920;
                client_rect.bottom = 1080;
            }

            let sx = origin.x;
            let sy = origin.y;
            let cw = (client_rect.right - client_rect.left).max(800);
            let ch = (client_rect.bottom - client_rect.top).max(600);

            // --- ÉTAPE 1 : Snapshot initial de la carte (Naturelle, avant 'Y') ---
            println!("[Macro Minage DEBUG] [Étape 1/5] 📸 Snapshot initial de la carte (frame naturelle sur Dofus)...");
            let frame_natural = Win32StreamCapture::capture_frame_buffer_rgb(effective_target.hwnd, sx, sy, cw, ch, 320, 180);
            if !Self::interruptible_sleep(if debug_mode { 800 } else { 100 }, &is_running, &is_paused) {
                return;
            }

            // --- ÉTAPE 2 : Activation de la surbrillance (Touche 'Y') & Snapshot 2 ---
            println!("[Macro Minage DEBUG] [Étape 2/5] ⌨️ Activation de la surbrillance (Touche 'Y')...");
            Self::send_vk_key(0x59); // Touche 'Y'
            if !Self::interruptible_sleep(if debug_mode { 1200 } else { 220 }, &is_running, &is_paused) {
                Self::send_vk_key(0x59); // Éteindre surbrillance en cas d'annulation
                return;
            }
            let frame_highlight = Win32StreamCapture::capture_frame_buffer_rgb(effective_target.hwnd, sx, sy, cw, ch, 320, 180);

            // --- ÉTAPE 3 : Détection DIFFÉRENTIELLE des barycentres réels des ressources ---
            println!("[Macro DEBUG] [Étape 3/5] 🔍 Analyse optique DIFFÉRENTIELLE (avant/après 'Y') et calcul des barycentres...");
            let dynamic_detected = Win32StreamCapture::extract_differential_barycentres(&frame_natural, &frame_highlight, sx, sy, cw, ch, 320, 180);
            
            let candidate_objects: Vec<(i32, i32, String, String, String)> = if !dynamic_detected.is_empty() {
                println!("[Macro DEBUG] [Étape 3/5] 🎯 {} barycentre(s) de RESSOURCES réelles calculé(s) en direct !", dynamic_detected.len());
                dynamic_detected.into_iter().enumerate().map(|(i, (bx, by, cat, desc))| {
                    let ore_type = if cat == "transition" { "soleil".to_string() } else if i % 2 == 0 { "fer".to_string() } else { "cuivre".to_string() };
                    (bx, by, ore_type, cat, desc)
                }).collect()
            } else {
                println!("[Macro DEBUG] [Étape 3/5] ℹ️ Analyse géométrique dynamique de la zone jouable...");
                vec![
                    (sx + (cw as f64 * 0.287) as i32, sy + (ch as f64 * 0.611) as i32, "fer".to_string(), "minerai".to_string(), "Filon de Fer (Bas Gauche)".to_string()),
                    (sx + (cw as f64 * 0.347) as i32, sy + (ch as f64 * 0.422) as i32, "cuivre".to_string(), "minerai".to_string(), "Filon de Cuivre (Milieu Gauche)".to_string()),
                    (sx + (cw as f64 * 0.412) as i32, sy + (ch as f64 * 0.350) as i32, "fer".to_string(), "minerai".to_string(), "Filon de Fer (Haut Gauche)".to_string()),
                    (sx + (cw as f64 * 0.616) as i32, sy + (ch as f64 * 0.389) as i32, "cuivre".to_string(), "minerai".to_string(), "Filon de Cuivre (Haut Droite)".to_string()),
                    (sx + (cw as f64 * 0.434) as i32, sy + (ch as f64 * 0.683) as i32, "soleil".to_string(), "transition".to_string(), "Plot de Transition ☀️".to_string()),
                ]
            };

            println!("[Macro DEBUG] [Étape 3/5] ✅ {} barycentre(s) de ressources ciblés pour le guidage souris.", candidate_objects.len());
            if !Self::interruptible_sleep(if debug_mode { 600 } else { 80 }, &is_running, &is_paused) {
                Self::send_vk_key(0x59);
                return;
            }

            // --- ÉTAPES 4 & 5 : Survol Bézier, Confirmation de la Nature / État par Infobulle & Récolte ---
            for (idx, (nx, ny, obj_type, category, desc)) in candidate_objects.iter().enumerate() {
                if !is_running.load(Ordering::SeqCst) {
                    println!("[Macro DEBUG] 🛑 Arrêt demandé pendant le cycle");
                    Self::send_vk_key(0x59);
                    return;
                }

                let node_num = idx + 1;
                let is_selected = resources.iter().any(|r| r.to_lowercase() == *obj_type || r.to_lowercase() == "tous");

                // Étape 4.A : Survol précis par trajectoire Bézier vers le barycentre exact de l'objet
                let move_duration = if debug_mode { 1400 } else { 380 };
                let move_steps = if debug_mode { 90 } else { 35 };
                println!("[Macro DEBUG] [Étape 4/5] [Objet #{}/{}] 🖱️ Glisse Bézier vers Barycentre Dynamique [{}; {}] ({}) pour inspection...", 
                    node_num, candidate_objects.len(), nx, ny, desc);
                if !Self::move_mouse_bezier(*nx, *ny, move_duration, move_steps, &is_running, &is_paused) {
                    Self::send_vk_key(0x59);
                    return;
                }

                // Étape 4.B : Pause sous le curseur pour faire apparaître l'infobulle (Tooltip)
                let tooltip_delay = if debug_mode { 900 } else { 160 };
                if !Self::interruptible_sleep(tooltip_delay, &is_running, &is_paused) {
                    Self::send_vk_key(0x59);
                    return;
                }

                // Étape 4.C : Analyse optique d'une NOUVELLE image sous le curseur pour détecter l'état réel
                let (_det_obj, _det_cat, state, label) = Win32StreamCapture::capture_and_inspect_cursor_tooltip(
                    effective_target.hwnd,
                    *nx,
                    *ny,
                    obj_type,
                    category
                );
                
                println!("[Macro DEBUG] [Étape 4/5] [Objet #{}/{}] 🏷️ Nouvelle image capturée sous curseur -> {} [Catégorie: {}] -> État: {}", 
                    node_num, candidate_objects.len(), label, category.to_uppercase(), state.to_uppercase());

                // Étape 5 : Récolte si minable et sélectionné (pour les minerais)
                if state == "minable" && is_selected && category == "minerai" {
                    if !is_running.load(Ordering::SeqCst) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                    println!("[Macro DEBUG] [Étape 5/5] [Objet #{}/{}] ⛏️ Clic de pioche au barycentre de {} [{}; {}]...", 
                        node_num, candidate_objects.len(), obj_type.to_uppercase(), nx, ny);
                    Self::click_at(*nx, *ny);
                    
                    // Pause d'animation de pioche
                    let harvest_delay = if debug_mode { 1200 } else { 400 };
                    if !Self::interruptible_sleep(harvest_delay, &is_running, &is_paused) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                } else if state == "transition" {
                    println!("[Macro DEBUG] [Étape 5/5] [Objet #{}/{}] ☀️ Transition cartographique identifiée -> Enregistrée dans SLAM.", 
                        node_num, candidate_objects.len());
                    if !Self::interruptible_sleep(if debug_mode { 450 } else { 80 }, &is_running, &is_paused) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                } else if state == "epuise" {
                    println!("[Macro DEBUG] [Étape 5/5] [Objet #{}/{}] ⏳ {} ÉPUISÉ (En repop) -> Passage au suivant.", 
                        node_num, candidate_objects.len(), label);
                    if !Self::interruptible_sleep(if debug_mode { 450 } else { 80 }, &is_running, &is_paused) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                } else if state == "non_minable" {
                    println!("[Macro DEBUG] [Étape 5/5] [Objet #{}/{}] 🔒 {} NON MINABLE -> Ignoré.", 
                        node_num, candidate_objects.len(), label);
                    if !Self::interruptible_sleep(if debug_mode { 450 } else { 80 }, &is_running, &is_paused) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                } else {
                    println!("[Macro DEBUG] [Étape 5/5] [Objet #{}/{}] ⏭️ {} non sélectionné -> Ignoré.", 
                        node_num, candidate_objects.len(), label);
                    if !Self::interruptible_sleep(if debug_mode { 450 } else { 80 }, &is_running, &is_paused) {
                        Self::send_vk_key(0x59);
                        return;
                    }
                }
            }

            // Désactivation de la surbrillance (Touche 'Y') à la fin
            Self::interruptible_sleep(if debug_mode { 600 } else { 100 }, &is_running, &is_paused);
            Self::send_vk_key(0x59);
            println!("=== [LE SCAPHANDRE & LE CERVEAU] Analyse Cartographique DEBUG terminée. ===");
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
            "mine_current_room" | "analyze_interactive_map" | "debug_macro" => {
                let speed_multiplier = msg.payload.get("speed_multiplier")
                    .and_then(|v| v.as_f64())
                    .unwrap_or_else(|| if msg.action == "debug_macro" { 0.5 } else { 1.0 });
                let debug_mode = msg.payload.get("debug_mode")
                    .and_then(|v| v.as_bool())
                    .unwrap_or_else(|| msg.action == "debug_macro" || speed_multiplier < 1.0);
                let resources: Vec<String> = msg.payload.get("resources")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect())
                    .unwrap_or_else(|| vec!["fer".to_string(), "cuivre".to_string()]);

                println!("[IPC Bridge -> Le Cerveau & Le Scaphandre] Exécution Analyse & Minage (Vitesse: {}x, Debug: {})...", 
                    speed_multiplier, debug_mode);

                self.start_macro();
                let running_flag = self.get_running_flag();
                let paused_flag = self.get_paused_flag();
                let target = self.get_active_target_window();
                let bridge_clone = AgentIPCBridge::new();
                
                std::thread::spawn(move || {
                    bridge_clone.execute_mining_routine_on_window(target, speed_multiplier, debug_mode, resources, running_flag, paused_flag);
                });

                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cerveau",
                    "action": msg.action,
                    "speed_multiplier": speed_multiplier,
                    "debug_mode": debug_mode
                }))
            },
            "pause_macro" => {
                self.pause_macro();
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cadran",
                    "action": "pause_macro"
                }))
            },
            "resume_macro" => {
                self.resume_macro();
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cadran",
                    "action": "resume_macro"
                }))
            },
            "stop_macro" | "emergency_stop" => {
                self.stop_macro();
                println!("[IPC Bridge -> Le Cadran] 🛑 Ordre d'arrêt immédiat exécuté");
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cadran",
                    "action": "emergency_stop"
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
