#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod fsm;
mod hotkeys;
mod ipc;
mod stream_capture;
mod window_state;

use fsm::{MapInfo, StateMachine, SupervisorState};
use hotkeys::{DirectionKey, HotkeyManager};
use ipc::{AgentIPCBridge, IPCMessage};
use stream_capture::{CaptureThumbnail, Win32StreamCapture};
use std::sync::Mutex;
use tauri::State;

struct AppState {
    fsm: StateMachine,
    hotkeys: HotkeyManager,
    ipc: AgentIPCBridge,
}

#[tauri::command]
fn get_supervisor_state(state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    Ok(format!("{:?}", app.fsm.get_state()))
}

#[tauri::command]
fn set_supervisor_state(new_state: String, state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    let target = match new_state.as_str() {
        "Navigation" => SupervisorState::Navigation,
        "Harvesting" => SupervisorState::Harvesting,
        "Combat" => SupervisorState::Combat,
        "Paused" => SupervisorState::Paused,
        "EmergencyStop" => SupervisorState::EmergencyStop,
        _ => SupervisorState::Idle,
    };
    if target == SupervisorState::Paused {
        app.ipc.pause_macro();
    } else if target == SupervisorState::Harvesting || target == SupervisorState::Navigation {
        app.ipc.resume_macro();
    } else if target == SupervisorState::EmergencyStop || target == SupervisorState::Idle {
        app.ipc.stop_macro();
    }
    let updated = app.fsm.transition_to(target)?;
    Ok(format!("{:?}", updated))
}

#[tauri::command]
fn get_current_map_info(state: State<'_, Mutex<AppState>>) -> Result<MapInfo, String> {
    let app = state.lock().unwrap();
    Ok(app.fsm.get_map_info())
}

#[tauri::command]
fn update_map_info(
    is_detected: bool,
    zone_name: String,
    pos_x: Option<i32>,
    pos_y: Option<i32>,
    area_level: Option<u32>,
    zone_bonus: Option<String>,
    sun_nodes_count: Option<u32>,
    error_message: Option<String>,
    state: State<'_, Mutex<AppState>>
) -> Result<MapInfo, String> {
    let app = state.lock().unwrap();
    let new_info = MapInfo {
        is_detected,
        zone_name,
        pos_x,
        pos_y,
        area_level,
        zone_bonus,
        sun_nodes_count: sun_nodes_count.unwrap_or(0),
        error_message,
    };
    Ok(app.fsm.update_map_info(new_info))
}

#[tauri::command]
fn trigger_directional_move(direction: String, window: tauri::Window, state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    let dir = match direction.as_str() {
        "Up" => DirectionKey::Up,
        "Down" => DirectionKey::Down,
        "Left" => DirectionKey::Left,
        _ => DirectionKey::Right,
    };
    let target = app.ipc.get_active_target_window();
    app.hotkeys.handle_directional_key(dir, target.hwnd);

    // Redonner le focus à la fenêtre de l'application IdleD pour enchaîner les commandes
    if let Err(e) = window.set_focus() {
        println!("[Superviseur Rust] Erreur réactivation focus application : {}", e);
    } else {
        println!("[Superviseur Rust] Focus restitué à l'application IdleD");
    }

    Ok(format!("Transition directionnelle {:?} initiée", direction))
}

#[tauri::command]
fn trigger_emergency_stop(state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    app.ipc.stop_macro();
    app.hotkeys.trigger_emergency_stop();
    let _ = app.fsm.transition_to(SupervisorState::EmergencyStop);
    println!("[Superviseur Rust] 🛑 Arrêt d'urgence appliqué sur FSM et moteur motrice");
    Ok("Arrêt d'urgence déclenché".into())
}

#[tauri::command]
fn send_ipc_message(agent: String, action: String, payload: serde_json::Value, state: State<'_, Mutex<AppState>>) -> Result<serde_json::Value, String> {
    let app = state.lock().unwrap();
    let msg = IPCMessage { agent, action, payload };
    app.ipc.send_to_agent(msg)
}

#[tauri::command]
fn get_active_target_window(state: State<'_, Mutex<AppState>>) -> Result<ipc::ActiveWindowInfo, String> {
    let app = state.lock().unwrap();
    Ok(app.ipc.get_active_target_window())
}

#[tauri::command]
fn get_stream_thumbnail(state: State<'_, Mutex<AppState>>) -> Result<CaptureThumbnail, String> {
    let app = state.lock().unwrap();
    let target = app.ipc.get_active_target_window();
    let (data_url_opt, detected_map) = Win32StreamCapture::capture_and_analyze(target.hwnd, &target.title, 260, 68);
    let data_url = data_url_opt.unwrap_or_default();
    
    // Mise à jour continue de l'état cartographique de l'application
    app.fsm.update_map_info(detected_map);

    let is_valid = !data_url.is_empty();
    Ok(CaptureThumbnail {
        is_valid,
        title: target.title,
        data_url,
    })
}

#[tauri::command]
fn adjust_window_size(width: f64, height: f64, window: tauri::Window) -> Result<(), String> {
    window.set_size(tauri::Size::Logical(tauri::LogicalSize { width, height }))
        .map_err(|e| e.to_string())
}

fn main() {
    let app_state = AppState {
        fsm: StateMachine::new(),
        hotkeys: HotkeyManager::new(),
        ipc: AgentIPCBridge::new(),
    };

    println!("[IdleD Superviseur Rust] Démarrage du système multi-agents...");

    tauri::Builder::default()
        .manage(Mutex::new(app_state))
        .invoke_handler(tauri::generate_handler![
            get_supervisor_state,
            set_supervisor_state,
            get_current_map_info,
            update_map_info,
            trigger_directional_move,
            trigger_emergency_stop,
            send_ipc_message,
            get_active_target_window,
            get_stream_thumbnail,
            adjust_window_size
        ])
        .run(tauri::generate_context!())
        .expect("Erreur lors du lancement de l'application Tauri IdleD");
}
