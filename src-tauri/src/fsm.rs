use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

/// Données cartographiques de la tuile et zone actuellement détectées sur Dofus Unity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MapInfo {
    pub is_detected: bool,
    pub zone_name: String,
    pub pos_x: Option<i32>,
    pub pos_y: Option<i32>,
    pub area_level: Option<u32>,
    pub zone_bonus: Option<String>,
    pub sun_nodes_count: u32,
    pub error_message: Option<String>,
}

impl MapInfo {
    pub fn none() -> Self {
        Self {
            is_detected: false,
            zone_name: "--".to_string(),
            pos_x: None,
            pos_y: None,
            area_level: None,
            zone_bonus: None,
            sun_nodes_count: 0,
            error_message: Some("Aucune détection active".to_string()),
        }
    }

    #[allow(dead_code)]
    pub fn detected(zone_name: &str, x: i32, y: i32, level: u32) -> Self {
        Self {
            is_detected: true,
            zone_name: zone_name.to_string(),
            pos_x: Some(x),
            pos_y: Some(y),
            area_level: Some(level),
            zone_bonus: None,
            sun_nodes_count: 0,
            error_message: None,
        }
    }
}

impl Default for MapInfo {
    fn default() -> Self {
        Self::none()
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fsm_initial_state() {
        let fsm = StateMachine::new();
        assert_eq!(fsm.get_state(), SupervisorState::Idle);
    }

    #[test]
    fn test_fsm_state_transitions() {
        let fsm = StateMachine::new();
        assert_eq!(fsm.transition_to(SupervisorState::Navigation).unwrap(), SupervisorState::Navigation);
        assert_eq!(fsm.transition_to(SupervisorState::Combat).unwrap(), SupervisorState::Combat);
        assert_eq!(fsm.transition_to(SupervisorState::EmergencyStop).unwrap(), SupervisorState::EmergencyStop);
    }

    #[test]
    fn test_map_info_updates() {
        let fsm = StateMachine::new();
        let default_info = fsm.get_map_info();
        assert!(!default_info.is_detected);
        assert_eq!(default_info.zone_name, "--");
        assert_eq!(default_info.pos_x, None);
        assert_eq!(default_info.pos_y, None);
        assert_eq!(default_info.area_level, None);

        let new_info = MapInfo::detected("Forêt d'Astrub", -5, -18, 20);
        let updated = fsm.update_map_info(new_info.clone());
        assert_eq!(updated, new_info);
        assert_eq!(fsm.get_map_info(), new_info);
    }

    #[test]
    fn test_map_info_detection_failed() {
        let fsm = StateMachine::new();
        let failed_info = MapInfo {
            is_detected: false,
            zone_name: "Détection impossible".to_string(),
            pos_x: None,
            pos_y: None,
            area_level: None,
            zone_bonus: None,
            sun_nodes_count: 0,
            error_message: Some("Fenêtre masquée".to_string()),
        };
        let updated = fsm.update_map_info(failed_info.clone());
        assert!(!updated.is_detected);
        assert_eq!(updated.error_message, Some("Fenêtre masquée".to_string()));
    }
}
