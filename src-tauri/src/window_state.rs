use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{PhysicalPosition, PhysicalSize, Window};

const CONFIG_PATH: &str = "../config/window_state.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WindowState {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}

impl Default for WindowState {
    fn default() -> Self {
        Self {
            x: 100,
            y: 100,
            width: 320,
            height: 720,
        }
    }
}

pub struct WindowStateStore;

impl WindowStateStore {
    fn config_file_path() -> PathBuf {
        PathBuf::from(CONFIG_PATH)
    }

    pub fn load() -> WindowState {
        let path = Self::config_file_path();
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(state) = serde_json::from_str::<WindowState>(&content) {
                    println!("[WindowState] Dimensions et position chargées : {:?}", state);
                    return state;
                }
            }
        }
        WindowState::default()
    }

    pub fn save(state: &WindowState) -> Result<(), String> {
        let path = Self::config_file_path();
        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let json = serde_json::to_string_pretty(state).map_err(|e| e.to_string())?;
        fs::write(&path, json).map_err(|e| e.to_string())?;
        println!("[WindowState] Dimensions et position sauvegardées : {:?}", state);
        Ok(())
    }

    pub fn apply_to_window(window: &Window) {
        let state = Self::load();
        let _ = window.set_position(PhysicalPosition::new(state.x, state.y));
        let _ = window.set_size(PhysicalSize::new(state.width, state.height));
    }

    pub fn update_from_window(window: &Window) {
        if let (Ok(pos), Ok(size)) = (window.outer_position(), window.outer_size()) {
            let state = WindowState {
                x: pos.x,
                y: pos.y,
                width: size.width,
                height: size.height,
            };
            let _ = Self::save(&state);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_window_state_default() {
        let state = WindowState::default();
        assert_eq!(state.width, 320);
        assert_eq!(state.height, 720);
    }

    #[test]
    fn test_window_state_serialization() {
        let state = WindowState {
            x: 250,
            y: 350,
            width: 320,
            height: 800,
        };
        let json = serde_json::to_string(&state).unwrap();
        let decoded: WindowState = serde_json::from_str(&json).unwrap();
        assert_eq!(state, decoded);
    }
}
