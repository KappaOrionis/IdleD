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

    /// Transmet et traite les commandes IPC transmises par l'interface vers les agents.
    pub fn send_to_agent(&self, msg: IPCMessage) -> Result<serde_json::Value, String> {
        println!("[IPC Bridge] Routage message vers l'agent '{}': action='{}', payload={:?}", 
            msg.agent, msg.action, msg.payload);
        
        match msg.action.as_str() {
            "send_chat_message" => {
                let text = msg.payload.get("text")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                println!("[IPC Bridge -> Le Scaphandre] Macro Chat déclenchée: '{}'", text);
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "scaphandre",
                    "action": "send_chat_message",
                    "executed_text": text
                }))
            },
            "travel_to" => {
                let x = msg.payload.get("x").and_then(|v| v.as_i64()).unwrap_or(0);
                let y = msg.payload.get("y").and_then(|v| v.as_i64()).unwrap_or(0);
                println!("[IPC Bridge -> Le Scaphandre] Commande Travel To: /travel {},{}", x, y);
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "scaphandre",
                    "action": "travel_to",
                    "destination": [x, y]
                }))
            },
            "emergency_stop" => {
                println!("[IPC Bridge -> Le Cadran] Ordre d'interruption immédiate reçu");
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": "cadran",
                    "action": "emergency_stop"
                }))
            },
            _ => {
                Ok(serde_json::json!({
                    "status": "success",
                    "agent": msg.agent,
                    "action": msg.action
                }))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ipc_chat_routing() {
        let bridge = AgentIPCBridge::new();
        let msg = IPCMessage {
            agent: "scaphandre".into(),
            action: "send_chat_message".into(),
            payload: serde_json::json!({ "text": "salut" }),
        };
        let res = bridge.send_to_agent(msg).unwrap();
        assert_eq!(res["status"], "success");
        assert_eq!(res["executed_text"], "salut");
    }

    #[test]
    fn test_ipc_travel_routing() {
        let bridge = AgentIPCBridge::new();
        let msg = IPCMessage {
            agent: "scaphandre".into(),
            action: "travel_to".into(),
            payload: serde_json::json!({ "x": 4, "y": 28 }),
        };
        let res = bridge.send_to_agent(msg).unwrap();
        assert_eq!(res["status"], "success");
        assert_eq!(res["destination"][0], 4);
        assert_eq!(res["destination"][1], 28);
    }
}
