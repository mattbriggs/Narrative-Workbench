//! Provenance record construction on the application side (SRS REQ-097).
//!
//! Mirrors the engine's provenance fields so the application layer can attach a
//! complete record at commit time.

use serde::{Deserialize, Serialize};

use crate::contract::{ActorRole, AuthorityState};

/// Origin of a change (NW ADD v1.1 Table 16).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Origin {
    Human,
    ImportedSource,
    DeterministicRule,
    ModelProposal,
    DerivedProjection,
}

/// A complete provenance record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Provenance {
    pub origin: Origin,
    pub actor: ActorRole,
    pub authority: AuthorityState,
    pub decision: String,
    pub reproducibility: String,
}

/// Build a provenance record, deriving reproducibility from origin.
///
/// # Contract
/// Returns `Err` when a model proposal is missing metadata is *not* enforced
/// here (the engine owns that rule, SRS REQ-194); this helper derives the
/// reproducibility label only.
pub fn build(origin: Origin, actor: ActorRole, authority: AuthorityState, decision: &str) -> Provenance {
    let reproducibility = match origin {
        Origin::DeterministicRule | Origin::DerivedProjection => "replayable",
        Origin::ModelProposal => "approximable",
        _ => "auditable",
    };
    Provenance {
        origin,
        actor,
        authority,
        decision: decision.to_string(),
        reproducibility: reproducibility.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contract::ActorRole;

    #[test]
    fn reproducibility_from_origin() {
        assert_eq!(
            build(Origin::DeterministicRule, ActorRole::NarrativeDesigner, AuthorityState::Allowed, "x").reproducibility,
            "replayable"
        );
        assert_eq!(
            build(Origin::ModelProposal, ActorRole::AiService, AuthorityState::ApprovalRequired, "x").reproducibility,
            "approximable"
        );
        assert_eq!(
            build(Origin::Human, ActorRole::NarrativeDesigner, AuthorityState::Allowed, "x").reproducibility,
            "auditable"
        );
    }

    #[test]
    fn provenance_roundtrips() {
        let p = build(Origin::Human, ActorRole::Critic, AuthorityState::Allowed, "accepted");
        let j = serde_json::to_string(&p).unwrap();
        let back: Provenance = serde_json::from_str(&j).unwrap();
        assert_eq!(back.decision, "accepted");
    }
}
