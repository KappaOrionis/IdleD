use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DirectionKey {
    Up,
    Down,
    Left,
    Right,
}

pub struct HotkeyManager;

impl HotkeyManager {
    pub fn new() -> Self {
        Self
    }

    /// Gère l'interception matérielle des touches directionnelles
    /// pour déclencher les changements de carte instantanés.
    pub fn handle_directional_key(&self, direction: DirectionKey) {
        println!("[Superviseur Hotkey] Touche directionnelle interceptée : {:?}", direction);
        // Transmet l'ordre à l'Agent d'Exécution (Le Scaphandre)
    }

    /// Arrêt d'urgence instantané (F12 / Global Hotkey)
    pub fn trigger_emergency_stop(&self) {
        println!("[Superviseur Hotkey] ARRÊT D'URGENCE DÉCLENCHÉ ! Interruption de tous les agents.");
    }
}
