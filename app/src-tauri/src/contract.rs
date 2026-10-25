//! Serde mirror of the engine's boundary contract (SRS REQ-161).
//!
//! These types serialize to the same JSON the Python engine produces and
//! consumes. The string values on each enum MUST match the engine's Pydantic
//! enums; `scripts/gen-contract.py` emits a JSON Schema from the engine models
//! so drift is caught in CI.

use serde::{Deserialize, Serialize};

/// The three operating modes (SRS §1.2).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    Composition,
    Criticism,
    Counterfactual,
}

/// Actor roles (SRS §2.3).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActorRole {
    NarrativeDesigner,
    Writer,
    Critic,
    Researcher,
    Reviewer,
    Administrator,
    AiService,
}

/// Whether the actor may carry a proposal forward (SRS §8.1).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AuthorityState {
    #[serde(rename = "allowed")]
    Allowed,
    #[serde(rename = "approvalRequired")]
    ApprovalRequired,
    #[serde(rename = "denied")]
    Denied,
}

/// Resolved command context (SRS REQ-130 step 1).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Context {
    pub work_id: Option<String>,
    pub branch_id: Option<String>,
    pub commit_id: Option<String>,
    pub mode: Mode,
    pub actor: ActorRole,
}

impl Context {
    /// Construct a minimal composition context for the given actor.
    pub fn new(actor: ActorRole) -> Self {
        Context {
            work_id: None,
            branch_id: None,
            commit_id: None,
            mode: Mode::Composition,
            actor,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mode_serializes_snake_case() {
        let j = serde_json::to_string(&Mode::Counterfactual).unwrap();
        assert_eq!(j, "\"counterfactual\"");
    }

    #[test]
    fn authority_uses_engine_spellings() {
        assert_eq!(
            serde_json::to_string(&AuthorityState::ApprovalRequired).unwrap(),
            "\"approvalRequired\""
        );
    }

    #[test]
    fn context_roundtrips() {
        let c = Context::new(ActorRole::Critic);
        let j = serde_json::to_string(&c).unwrap();
        let back: Context = serde_json::from_str(&j).unwrap();
        assert_eq!(back.actor, ActorRole::Critic);
        assert_eq!(back.mode, Mode::Composition);
    }
}
