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
                        let info = ActiveWindowInfo { hwnd: fg, title };
                        let mut lock = self.last_target_window.lock().unwrap();
                        *lock = Some(info.clone());
                        return info;
                    }
                }
            }

            // Si IdleD a le focus, vérifier si on a déjà une fenêtre mémorisée
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

    /// Focus la fenêtre cible
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
            SetForegroundWindow(target_hwnd);
            BringWindowToTop(target_hwnd);

            if fore_thread != 0 && fore_thread != current_thread {
                AttachThreadInput(current_thread, fore_thread, 0);
            }
            if target_thread != 0 && target_thread != current_thread {
                AttachThreadInput(current_thread, target_thread, 0);
            }

            std::thread::sleep(Duration::from_millis(90));
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
            Self::send_vk_key(VK_RETURN);
        }

        Ok(())
    }

    /// Transmet et traite les commandes IPC
    pub fn send_to_agent(&self, msg: IPCMessage) -> Result<serde_json::Value, String> {
        println!("[IPC Bridge] Routage message vers l'agent '{}': action='{}', payload={:?}", 
            msg.agent, msg.action, msg.payload);
        
        match msg.action.as_str() {
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
