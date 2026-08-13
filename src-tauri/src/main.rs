#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod fsm;
mod hotkeys;
mod ipc;

use fsm::{StateMachine, SupervisorState};
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
            trigger_directional_move
        ])
        .run(tauri::generate_context!())
        .expect("Erreur lors du lancement de l'application Tauri IdleD");
}
