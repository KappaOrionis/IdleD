use serde::{Deserialize, Serialize};

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct WindowState {
    pub width: u32,
    pub height: u32,
}

impl Default for WindowState {
    fn default() -> Self {
        Self {
            width: 780,
            height: 740,
        }
    }
}

#[allow(dead_code)]
pub struct WindowStateStore;

impl WindowStateStore {
    // La mémorisation de la taille et position de la fenêtre Windows a été supprimée selon la demande utilisateur.
    // L'application s'ouvre avec les dimensions par défaut.
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_window_state_default() {
        let state = WindowState::default();
        assert_eq!(state.width, 780);
        assert_eq!(state.height, 740);
    }
}
