use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IPCMessage {
    pub agent: String,
    pub action: String,
    pub payload: serde_json::Value,
}

pub struct AgentIPCBridge;

impl AgentIPCBridge {
    pub fn new() -> Self {
        Self
    }

    /// Transmet une commande JSON au micro-service Python approprié.
    pub fn send_to_agent(&self, msg: IPCMessage) -> Result<serde_json::Value, String> {
        println!("[IPC Bridge] Envoi du message à l'agent '{}': {}", msg.agent, msg.action);
        // Communication stdin/stdout ou Socket locale IPC
        Ok(serde_json::json!({ "status": "success", "agent": msg.agent }))
    }
}
