//! Authority decisions (SRS §2.3, REQ-174).
//!
//! Maps an actor role and an action to an [`AuthorityState`]. Authority is part
//! of every mutating use case, not a separate afterthought. AI services never
//! have independent mutation authority (SRS REQ-100..103).

use crate::contract::{ActorRole, AuthorityState};

/// Mutating actions subject to authority checks.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    /// Change canonical creative state (commit a composition delta).
    CommitCanonical,
    /// Create a claim or interpretive branch.
    CreateInterpretation,
    /// Create a constrained experiment branch.
    CreateExperiment,
    /// Edit prose (model changes still require reconciliation).
    EditProse,
    /// Mutate an imported source edition (never allowed).
    MutateSource,
    /// Manage workspace policy.
    ManagePolicy,
}

/// Decide the authority state for a role attempting an action.
///
/// # Contract
/// Returns [`AuthorityState::Allowed`] when the role may perform the action
/// directly, [`AuthorityState::ApprovalRequired`] when a proposal needs an
/// authorized human approver, and [`AuthorityState::Denied`] when the role may
/// never perform it. [`Action::MutateSource`] is `Denied` for every role
/// (SRS REQ-177).
pub fn decide(role: ActorRole, action: Action) -> AuthorityState {
    use ActorRole::*;
    use Action::*;
    match action {
        MutateSource => AuthorityState::Denied,
        CommitCanonical => match role {
            NarrativeDesigner => AuthorityState::Allowed,
            Writer => AuthorityState::ApprovalRequired,
            AiService => AuthorityState::Denied,
            _ => AuthorityState::Denied,
        },
        CreateInterpretation => match role {
            Critic | Researcher | NarrativeDesigner => AuthorityState::Allowed,
            AiService => AuthorityState::Denied,
            _ => AuthorityState::ApprovalRequired,
        },
        CreateExperiment => match role {
            Researcher | Critic | NarrativeDesigner => AuthorityState::Allowed,
            AiService => AuthorityState::Denied,
            _ => AuthorityState::ApprovalRequired,
        },
        EditProse => match role {
            Writer | NarrativeDesigner => AuthorityState::Allowed,
            AiService => AuthorityState::Denied,
            _ => AuthorityState::ApprovalRequired,
        },
        ManagePolicy => match role {
            Administrator => AuthorityState::Allowed,
            _ => AuthorityState::Denied,
        },
    }
}

/// A visible reason string for a denied or approval-required action
/// (SRS REQ-080). Used by the UI to explain a disabled control.
pub fn reason(role: ActorRole, action: Action) -> Option<String> {
    match decide(role, action) {
        AuthorityState::Allowed => None,
        AuthorityState::ApprovalRequired => {
            Some(format!("{action:?} by {role:?} requires an authorized approver"))
        }
        AuthorityState::Denied => Some(format!("{action:?} is not permitted for {role:?}")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contract::ActorRole::*;

    #[test]
    fn source_never_mutable() {
        for role in [NarrativeDesigner, Critic, Administrator, AiService] {
            assert_eq!(decide(role, Action::MutateSource), AuthorityState::Denied);
        }
    }

    #[test]
    fn designer_commits_canonical() {
        assert_eq!(decide(NarrativeDesigner, Action::CommitCanonical), AuthorityState::Allowed);
        assert_eq!(decide(Writer, Action::CommitCanonical), AuthorityState::ApprovalRequired);
        assert_eq!(decide(AiService, Action::CommitCanonical), AuthorityState::Denied);
    }

    #[test]
    fn ai_has_no_mutation_authority() {
        for action in [
            Action::CommitCanonical,
            Action::CreateInterpretation,
            Action::CreateExperiment,
            Action::EditProse,
        ] {
            assert_eq!(decide(AiService, action), AuthorityState::Denied);
        }
    }

    #[test]
    fn reviewer_needs_approval_for_interpretation() {
        assert_eq!(decide(Reviewer, Action::CreateInterpretation), AuthorityState::ApprovalRequired);
    }

    #[test]
    fn admin_manages_policy_only() {
        assert_eq!(decide(Administrator, Action::ManagePolicy), AuthorityState::Allowed);
        assert_eq!(decide(Administrator, Action::CommitCanonical), AuthorityState::Denied);
    }

    #[test]
    fn reason_text_present_when_not_allowed() {
        assert!(reason(AiService, Action::CommitCanonical).unwrap().contains("not permitted"));
        assert!(reason(Writer, Action::CommitCanonical).unwrap().contains("requires"));
        assert!(reason(NarrativeDesigner, Action::CommitCanonical).is_none());
    }
}
