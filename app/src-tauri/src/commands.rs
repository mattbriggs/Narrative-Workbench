//! Intention-revealing commands (SRS REQ-161).
//!
//! Each command has one identity and an idempotency key so a mutation is
//! applied at most once. The frontend emits commands; it never writes graph or
//! repository records directly (SRS REQ-160).

use serde::{Deserialize, Serialize};

/// The command kinds the application layer accepts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum Command {
    ProposeTransition { target_unit: String },
    AcceptTrajectory { candidate_id: String },
    ApplyOperator { operator: String, scope: String },
    AnchorEvidence { source_edition_id: String, region: String },
    CreateBranch { from_commit: String, name: String },
    Commit { branch_id: String, parent: Option<String> },
}

/// A command paired with its idempotency key.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandEnvelope {
    pub idempotency_key: String,
    pub command: Command,
}

impl CommandEnvelope {
    /// Wrap a command with an idempotency key.
    pub fn new(idempotency_key: &str, command: Command) -> Self {
        CommandEnvelope {
            idempotency_key: idempotency_key.to_string(),
            command,
        }
    }
}

/// Deduplicating sink: records applied keys so a replay is a no-op.
#[derive(Default)]
pub struct CommandLog {
    applied: std::collections::HashSet<String>,
}

impl CommandLog {
    /// Create an empty log.
    pub fn new() -> Self {
        CommandLog::default()
    }

    /// Apply a command once. Returns `true` if applied, `false` if a duplicate
    /// idempotency key made it a no-op (SRS REQ-161).
    pub fn apply(&mut self, env: &CommandEnvelope) -> bool {
        self.applied.insert(env.idempotency_key.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn idempotency_key_dedupes() {
        let mut log = CommandLog::new();
        let env = CommandEnvelope::new("k1", Command::AcceptTrajectory { candidate_id: "B".into() });
        assert!(log.apply(&env));
        assert!(!log.apply(&env)); // duplicate is a no-op
    }

    #[test]
    fn command_tag_serializes() {
        let c = Command::CreateBranch { from_commit: "c1".into(), name: "exp".into() };
        let j = serde_json::to_string(&c).unwrap();
        assert!(j.contains("\"kind\":\"create_branch\""));
    }
}
