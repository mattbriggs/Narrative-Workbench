"""Pydantic boundary contracts for the engine.

These models define the typed shapes exchanged across the application/engine
boundary (SRS SS8). They are the single source for the JSON contract; the Rust
application layer mirrors them with ``serde`` (SRS REQ-161), and
``scripts/gen-contract.py`` emits a JSON Schema from them so drift fails CI.
"""

from nw_engine.contracts.models import (
    ActorRole,
    AuthorityState,
    BranchState,
    Candidate,
    Commit,
    Comparison,
    ComparisonRow,
    Context,
    Diff,
    Event,
    EvidenceAnchor,
    HardFailure,
    Interpretation,
    JobState,
    Mode,
    ModalModel,
    ModelTransition,
    Origin,
    Proposal,
    ProposalState,
    ProvenanceRecord,
    Situation,
    SoftGoal,
    StateAssertion,
    StateObject,
    Transition,
    Trajectory,
    ValidationResult,
    ValidationState,
)
from nw_engine.contracts.rpc import Request, Response

__all__ = [
    "ActorRole",
    "AuthorityState",
    "BranchState",
    "Candidate",
    "Commit",
    "Comparison",
    "ComparisonRow",
    "Context",
    "Diff",
    "Event",
    "EvidenceAnchor",
    "HardFailure",
    "Interpretation",
    "JobState",
    "Mode",
    "ModalModel",
    "ModelTransition",
    "Origin",
    "Proposal",
    "ProposalState",
    "ProvenanceRecord",
    "Request",
    "Response",
    "Situation",
    "SoftGoal",
    "StateAssertion",
    "StateObject",
    "Transition",
    "Trajectory",
    "ValidationResult",
    "ValidationState",
]
