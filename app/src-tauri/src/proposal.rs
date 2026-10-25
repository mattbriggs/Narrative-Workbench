//! The proposal lifecycle state machine (SRS §3.8, REQ-071).
//!
//! This is the only permitted route from draft intent to durable state.
//! Acceptance is distinct from commit (SRS REQ-076): `Accepted` does not change
//! canonical state; only the `Committed` transition persists the delta. An event
//! with no permitted transition causes no mutation and yields a visible reason
//! (SRS REQ-188).

use serde::{Deserialize, Serialize};

/// Proposal lifecycle states.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProposalState {
    None,
    Draft,
    Submitted,
    Validating,
    Rejected,
    AwaitingApproval,
    RevisionRequested,
    Accepted,
    Committing,
    Committed,
}

/// Events that drive the lifecycle.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Event {
    MutatingGesture,
    Submit { schema_complete: bool, may_propose: bool },
    ContextResolved,
    HardInvariantFails,
    HardChecksPass,
    RequestRevision,
    Edit,
    Approve { authorized: bool },
    Commit { parent_unchanged: bool, conflict_resolved: bool },
}

/// The outcome of attempting a transition: either a new state, or a refusal
/// carrying a visible reason (SRS REQ-188).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Transition {
    To(ProposalState),
    NoMutation(String),
}

/// Apply an event to a state, returning the resulting transition.
///
/// # Contract
/// Never panics. An unhandled (state, event) pair returns
/// [`Transition::NoMutation`] with a human-readable reason; the caller leaves
/// canonical state unchanged and surfaces the reason.
pub fn step(state: ProposalState, event: Event) -> Transition {
    use Event::*;
    use ProposalState::*;
    match (state, event) {
        (None, MutatingGesture) => Transition::To(Draft),
        (Draft, Submit { schema_complete, may_propose }) => {
            if schema_complete && may_propose {
                Transition::To(Submitted)
            } else if !schema_complete {
                Transition::NoMutation("proposal schema is incomplete".into())
            } else {
                Transition::NoMutation("actor may not propose".into())
            }
        }
        (Submitted, ContextResolved) => Transition::To(Validating),
        (Validating, HardInvariantFails) => Transition::To(Rejected),
        (Validating, HardChecksPass) => Transition::To(AwaitingApproval),
        (AwaitingApproval, RequestRevision) => Transition::To(RevisionRequested),
        (RevisionRequested, Edit) => Transition::To(Draft),
        (AwaitingApproval, Approve { authorized }) => {
            if authorized {
                Transition::To(Accepted)
            } else {
                Transition::NoMutation("commit requires narrative designer authority".into())
            }
        }
        (Accepted, Commit { parent_unchanged, conflict_resolved }) => {
            if parent_unchanged || conflict_resolved {
                Transition::To(Committed)
            } else {
                // Parent changed and unresolved: open the conflict resolver;
                // canonical state is unchanged (SRS REQ-078).
                Transition::NoMutation("parent commit changed; resolve the semantic conflict".into())
            }
        }
        (s, e) => Transition::NoMutation(format!("no transition from {s:?} on {e:?}")),
    }
}

/// True when a state means canonical state has been persisted.
pub fn is_durable(state: ProposalState) -> bool {
    matches!(state, ProposalState::Committed)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ProposalState::*;

    #[test]
    fn happy_path_to_commit() {
        let mut s = None;
        s = expect_to(step(s, Event::MutatingGesture));
        assert_eq!(s, Draft);
        s = expect_to(step(s, Event::Submit { schema_complete: true, may_propose: true }));
        assert_eq!(s, Submitted);
        s = expect_to(step(s, Event::ContextResolved));
        s = expect_to(step(s, Event::HardChecksPass));
        assert_eq!(s, AwaitingApproval);
        s = expect_to(step(s, Event::Approve { authorized: true }));
        assert_eq!(s, Accepted);
        // Acceptance is not persistence.
        assert!(!is_durable(s));
        s = expect_to(step(s, Event::Commit { parent_unchanged: true, conflict_resolved: false }));
        assert!(is_durable(s));
    }

    #[test]
    fn incomplete_schema_blocks_submit() {
        assert_eq!(
            step(Draft, Event::Submit { schema_complete: false, may_propose: true }),
            Transition::NoMutation("proposal schema is incomplete".into())
        );
    }

    #[test]
    fn unauthorized_may_not_propose() {
        assert_eq!(
            step(Draft, Event::Submit { schema_complete: true, may_propose: false }),
            Transition::NoMutation("actor may not propose".into())
        );
    }

    #[test]
    fn hard_failure_rejects() {
        assert_eq!(step(Validating, Event::HardInvariantFails), Transition::To(Rejected));
    }

    #[test]
    fn revision_loop() {
        let s = expect_to(step(AwaitingApproval, Event::RequestRevision));
        assert_eq!(s, RevisionRequested);
        assert_eq!(step(s, Event::Edit), Transition::To(Draft));
    }

    #[test]
    fn unauthorized_approve_is_refused() {
        assert_eq!(
            step(AwaitingApproval, Event::Approve { authorized: false }),
            Transition::NoMutation("commit requires narrative designer authority".into())
        );
    }

    #[test]
    fn parent_changed_opens_conflict() {
        assert_eq!(
            step(Accepted, Event::Commit { parent_unchanged: false, conflict_resolved: false }),
            Transition::NoMutation("parent commit changed; resolve the semantic conflict".into())
        );
        assert_eq!(
            step(Accepted, Event::Commit { parent_unchanged: false, conflict_resolved: true }),
            Transition::To(Committed)
        );
    }

    #[test]
    fn unhandled_event_is_no_mutation() {
        match step(Committed, Event::MutatingGesture) {
            Transition::NoMutation(reason) => assert!(reason.contains("no transition")),
            _ => panic!("expected no mutation"),
        }
    }

    fn expect_to(t: Transition) -> ProposalState {
        match t {
            Transition::To(s) => s,
            Transition::NoMutation(r) => panic!("unexpected no-mutation: {r}"),
        }
    }
}
