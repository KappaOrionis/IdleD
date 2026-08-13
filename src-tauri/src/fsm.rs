use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

/// Données cartographiques de la tuile et zone actuellement détectées sur Dofus Unity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MapInfo {
    pub zone_name: String,
    pub pos_x: i32,
    pub pos_y: i32,
    pub area_level: u32,
}

impl Default for MapInfo {
    fn default() -> Self {
        Self {
            zone_name: "Baie de Sufokia (Sufokia)".to_string(),
            pos_x: 12,
            pos_y: 27,
            area_level: 10,
        }
    }
}

/// États de la Machine à États Finis (FSM) du Superviseur (Le Cadran).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SupervisorState {
    Idle,
    Navigation,
    Harvesting,
    Combat,
    Paused,
    EmergencyStop,
}

pub struct StateMachine {
    current_state: Arc<Mutex<SupervisorState>>,
    current_map_info: Arc<Mutex<MapInfo>>,
}

impl StateMachine {
    pub fn new() -> Self {
        Self {
            current_state: Arc::new(Mutex::new(SupervisorState::Idle)),
            current_map_info: Arc::new(Mutex::new(MapInfo::default())),
        }
    }

    pub fn get_state(&self) -> SupervisorState {
        *self.current_state.lock().unwrap()
    }

    pub fn get_map_info(&self) -> MapInfo {
        self.current_map_info.lock().unwrap().clone()
    }

    pub fn update_map_info(&self, new_info: MapInfo) -> MapInfo {
        let mut info = self.current_map_info.lock().unwrap();
        *info = new_info.clone();
        info.clone()
    }

    pub fn transition_to(&self, new_state: SupervisorState) -> Result<SupervisorState, String> {
        let mut state = self.current_state.lock().unwrap();
        println!("[Le Cadran FSM] Transition d'état : {:?} -> {:?}", *state, new_state);
        *state = new_state;
        Ok(*state)
    }
}
