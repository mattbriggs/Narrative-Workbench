//! Engine request/response envelope over the line-delimited JSON contract
//! (SRS REQ-160). The desktop target spawns the Python sidecar and exchanges
//! these envelopes over stdio; here we cover construction and (de)serialization,
//! which is the part that must stay in lock-step with the engine.

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::contract::Context;

/// An application-to-engine command envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Request {
    pub op: String,
    pub op_id: String,
    pub context: Context,
    pub payload: Value,
}

impl Request {
    /// Build a request with an idempotency key (SRS REQ-161).
    pub fn new(op: &str, op_id: &str, context: Context, payload: Value) -> Self {
        Request {
            op: op.to_string(),
            op_id: op_id.to_string(),
            context,
            payload,
        }
    }

    /// Serialize to a single contract line (newline-terminated).
    pub fn to_line(&self) -> String {
        let mut s = serde_json::to_string(self).expect("Request is always serializable");
        s.push('\n');
        s
    }
}

/// A structured engine error.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseError {
    pub code: String,
    pub message: String,
    pub scope: Option<String>,
}

/// An engine-to-application result envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Response {
    pub op_id: String,
    pub ok: bool,
    #[serde(default)]
    pub result: Value,
    #[serde(default)]
    pub error: Option<ResponseError>,
}

impl Response {
    /// Parse a contract line from the engine.
    pub fn from_line(line: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(line.trim())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contract::ActorRole;
    use serde_json::json;

    #[test]
    fn request_line_is_newline_terminated_json() {
        let r = Request::new("propose", "o1", Context::new(ActorRole::NarrativeDesigner), json!({"k": 1}));
        let line = r.to_line();
        assert!(line.ends_with('\n'));
        let parsed: serde_json::Value = serde_json::from_str(line.trim()).unwrap();
        assert_eq!(parsed["op"], "propose");
        assert_eq!(parsed["op_id"], "o1");
    }

    #[test]
    fn response_parses_ok_and_error() {
        let ok = Response::from_line("{\"op_id\":\"o1\",\"ok\":true,\"result\":{\"x\":1}}").unwrap();
        assert!(ok.ok && ok.error.is_none());
        let err = Response::from_line(
            "{\"op_id\":\"o2\",\"ok\":false,\"error\":{\"code\":\"HARD_INVARIANT\",\"message\":\"bad\",\"scope\":\"s\"}}",
        )
        .unwrap();
        assert_eq!(err.error.unwrap().code, "HARD_INVARIANT");
    }

    #[test]
    fn malformed_line_errors() {
        assert!(Response::from_line("not json").is_err());
    }
}
