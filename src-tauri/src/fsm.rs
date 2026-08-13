use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

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
}

impl StateMachine {
    pub fn new() -> Self {
        Self {
            current_state: Arc::new(Mutex::new(SupervisorState::Idle)),
        }
    }

    pub fn get_state(&self) -> SupervisorState {
        *self.current_state.lock().unwrap()
    }

    pub fn transition_to(&self, new_state: SupervisorState) -> Result<SupervisorState, String> {
        let mut state = self.current_state.lock().unwrap();
        println!("[Le Cadran FSM] Transition d'état : {:?} -> {:?}", *state, new_state);
        *state = new_state;
        Ok(*state)
    }
}
