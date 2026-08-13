#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod fsm;
mod hotkeys;
mod ipc;

use fsm::{MapInfo, StateMachine, SupervisorState};
use hotkeys::{DirectionKey, HotkeyManager};
use ipc::{AgentIPCBridge, IPCMessage};
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
    let updated = app.fsm.transition_to(target)?;
    Ok(format!("{:?}", updated))
}

#[tauri::command]
fn get_current_map_info(state: State<'_, Mutex<AppState>>) -> Result<MapInfo, String> {
    let app = state.lock().unwrap();
    Ok(app.fsm.get_map_info())
}

#[tauri::command]
fn update_map_info(zone_name: String, pos_x: i32, pos_y: i32, area_level: u32, state: State<'_, Mutex<AppState>>) -> Result<MapInfo, String> {
    let app = state.lock().unwrap();
    let new_info = MapInfo {
        zone_name,
        pos_x,
        pos_y,
        area_level,
    };
    Ok(app.fsm.update_map_info(new_info))
}

#[tauri::command]
fn trigger_directional_move(direction: String, state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    let dir = match direction.as_str() {
        "Up" => DirectionKey::Up,
        "Down" => DirectionKey::Down,
        "Left" => DirectionKey::Left,
        _ => DirectionKey::Right,
    };
    app.hotkeys.handle_directional_key(dir);
    Ok(format!("Transition directionnelle {:?} initiée", direction))
}

#[tauri::command]
fn trigger_emergency_stop(state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app = state.lock().unwrap();
    app.hotkeys.trigger_emergency_stop();
    let _ = app.fsm.transition_to(SupervisorState::EmergencyStop);
    Ok("Arrêt d'urgence déclenché".into())
}

#[tauri::command]
fn send_ipc_message(agent: String, action: String, payload: serde_json::Value, state: State<'_, Mutex<AppState>>) -> Result<serde_json::Value, String> {
    let app = state.lock().unwrap();
    let msg = IPCMessage { agent, action, payload };
    app.ipc.send_to_agent(msg)
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
            send_ipc_message
        ])
        .run(tauri::generate_context!())
        .expect("Erreur lors du lancement de l'application Tauri IdleD");
}
