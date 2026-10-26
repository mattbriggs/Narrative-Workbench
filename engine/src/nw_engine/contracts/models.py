"""Typed boundary models.

Every model is a :class:`pydantic.BaseModel` so it validates on construction and
serializes to the JSON contract. Field names are the observable contract (SRS
SS8.1); implementation names may differ only if tests expose equivalent values.

:framework integration: these models are the engine half of the cross-process
    contract. Keep them free of engine internals (no NetworkX objects) so they
    serialize cleanly to the Rust application layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from nw_engine.domain.vocabulary import AssertionLevel, RelationshipType, TransitionClass


class Mode(str, Enum):
    """The three operating modes (SRS SS1.2)."""

    COMPOSITION = "composition"
    CRITICISM = "criticism"
    COUNTERFACTUAL = "counterfactual"


class ActorRole(str, Enum):
    """Actor roles and their mutation authority (SRS SS2.3)."""

    NARRATIVE_DESIGNER = "narrative_designer"
    WRITER = "writer"
    CRITIC = "critic"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    ADMINISTRATOR = "administrator"
    AI_SERVICE = "ai_service"


class Origin(str, Enum):
    """Provenance origin of a change (NW ADD v1.1 Table 16)."""

    HUMAN = "human"
    IMPORTED_SOURCE = "imported_source"
    DETERMINISTIC_RULE = "deterministic_rule"
    MODEL_PROPOSAL = "model_proposal"
    DERIVED_PROJECTION = "derived_projection"


class ProposalState(str, Enum):
    """Proposal lifecycle states (SRS REQ-071)."""

    NONE = "none"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    REJECTED = "rejected"
    AWAITING_APPROVAL = "awaitingApproval"
    REVISION_REQUESTED = "revisionRequested"
    ACCEPTED = "accepted"
    COMMITTING = "committing"
    COMMITTED = "committed"


class ValidationState(str, Enum):
    """Deterministic validation status."""

    IDLE = "idle"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class AuthorityState(str, Enum):
    """Whether the actor may carry a proposal forward."""

    ALLOWED = "allowed"
    APPROVAL_REQUIRED = "approvalRequired"
    DENIED = "denied"


class BranchState(str, Enum):
    """Branch lifecycle states (SRS REQ-093)."""

    ACTIVE = "active"
    IN_REVIEW = "inReview"
    MERGE_READY = "mergeReady"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class JobState(str, Enum):
    """Long-job lifecycle states (SRS REQ-110)."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETE = "complete"


class Context(BaseModel):
    """Resolved command context (SRS REQ-130 step 1)."""

    work_id: Optional[str] = None
    branch_id: Optional[str] = None
    commit_id: Optional[str] = None
    mode: Mode = Mode.COMPOSITION
    actor: ActorRole = ActorRole.NARRATIVE_DESIGNER


class StateObject(BaseModel):
    """A narrative object -- a **body**. Its ``mass`` is resistance to change."""

    id: str
    kind: str
    label: str = ""
    mass: float = Field(default=1.0, ge=0.0)


class StateAssertion(BaseModel):
    """A time-, model-, and scope-qualified value held by a body."""

    id: str
    object_id: str
    key: str
    value: Any
    model_id: Optional[str] = None
    scope: Optional[str] = None
    story_time: int = 0


class Event(BaseModel):
    """A disturbance or occurrence in story/discourse/authoring/analysis time."""

    id: str
    unit_id: Optional[str] = None
    description: str = ""
    story_time: int = 0
    discourse_time: Optional[int] = None


class Transition(BaseModel):
    """A proposed or accepted change -- an **impulse** (SRS REQ-013, REQ-131).

    ``kind`` is ``"ordinary"`` or ``"model"``. ``constraints`` are the **gates**
    the transition must satisfy. ``order`` numbers impulses applied to the field.
    """

    id: str
    order: int = 0
    kind: str = "ordinary"
    tclass: TransitionClass = TransitionClass.CAUSAL
    description: str = ""
    preconditions: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    causes: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    affected_models: list[str] = Field(default_factory=list)
    event_id: Optional[str] = None
    provenance_ref: Optional[str] = None


class Situation(BaseModel):
    """A possible-world node inside a modal model."""

    id: str
    propositions: dict[str, bool] = Field(default_factory=dict)


class ModalModel(BaseModel):
    """A named possibility structure ``M = (W, R, V)`` (SRS REQ-020).

    ``scope`` is the **boundary** of the active model. ``accessibility`` maps a
    situation id to the situations it can reach, with an optional weight.
    """

    id: str
    scope: str
    owner: Optional[str] = None
    situations: list[Situation] = Field(default_factory=list)
    accessibility: dict[str, list[str]] = Field(default_factory=dict)
    current: Optional[str] = None
    depth: int = 1


class ModelTransition(BaseModel):
    """A change to a modal model (an epiphany when declared) (SRS REQ-131)."""

    id: str
    trigger: str
    affected_model: str
    invalidated: list[str] = Field(default_factory=list)
    reinterpreted_events: list[str] = Field(default_factory=list)
    new_affordances: list[str] = Field(default_factory=list)
    is_epiphany: bool = False


class EvidenceAnchor(BaseModel):
    """A **pin** -- a stable reference into a frozen source edition (SRS REQ-051)."""

    id: str
    source_edition_id: str
    region: str
    fingerprint: str
    resolves: bool = True


class Interpretation(BaseModel):
    """An Observation, Finding, or Claim on an interpretive branch (SRS REQ-054)."""

    id: str
    level: AssertionLevel
    text: str
    proposer: Origin = Origin.HUMAN
    supporting_anchors: list[str] = Field(default_factory=list)
    contradicting_anchors: list[str] = Field(default_factory=list)
    lens: Optional[str] = None
    certainty: str = "contestable"
    branch_id: Optional[str] = None
    accepted: bool = False


class SoftGoal(BaseModel):
    """A scored, non-blocking goal (SRS REQ-079)."""

    name: str
    score: float
    rationale: str = ""


class HardFailure(BaseModel):
    """A blocking invariant violation (SRS REQ-074)."""

    rule: str
    scope: str
    explanation: str
    alternatives: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """The deterministic validation outcome for a proposal (SRS SS8.3)."""

    passed: bool
    hard_failures: list[HardFailure] = Field(default_factory=list)
    soft_goals: list[SoftGoal] = Field(default_factory=list)
    uncertainty: Optional[str] = None
    validator_version: str = "0.1.0"


class Candidate(BaseModel):
    """One candidate trajectory presented to the user (SRS REQ-044)."""

    id: str
    label: str
    transitions: list[Transition] = Field(default_factory=list)
    changed_objects: list[str] = Field(default_factory=list)
    propagation_frontier: list[str] = Field(default_factory=list)
    validation: Optional[ValidationResult] = None


class Trajectory(BaseModel):
    """An ordered candidate sequence considered together (SRS REQ-044)."""

    id: str
    candidate_ids: list[str] = Field(default_factory=list)


class ProvenanceRecord(BaseModel):
    """The seven provenance fields (NW ADD v1.1 Table 16, SRS REQ-097)."""

    origin: Origin
    actor: ActorRole
    authority: AuthorityState
    inputs: dict[str, Any] = Field(default_factory=dict)
    decision: str = ""
    alternatives: list[str] = Field(default_factory=list)
    model_metadata: Optional[dict[str, Any]] = None
    reproducibility: str = "auditable"


class Commit(BaseModel):
    """An immutable set of accepted operations against one parent (SRS REQ-090)."""

    id: str
    parent_id: Optional[str]
    branch_id: str
    actor: ActorRole
    authority: AuthorityState
    op_ids: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord
    accepted_alternatives: list[str] = Field(default_factory=list)
    message: str = ""


class Proposal(BaseModel):
    """A not-yet-durable delta moving through the lifecycle (SRS REQ-070)."""

    id: str
    origin: Origin = Origin.HUMAN
    state: ProposalState = ProposalState.DRAFT
    payload: dict[str, Any] = Field(default_factory=dict)
    frozen: bool = False
    authority_required: AuthorityState = AuthorityState.APPROVAL_REQUIRED
    alternatives: list[str] = Field(default_factory=list)
    predecessor_id: Optional[str] = None
    model_metadata: Optional[dict[str, Any]] = None


class Diff(BaseModel):
    """A single labeled change in a comparison (SRS REQ-064)."""

    label: str  # Added | Removed | Changed | Invariant
    subject: str
    before: Any = None
    after: Any = None


class ComparisonRow(BaseModel):
    """One dimension row of the counterfactual matrix (SRS REQ-063)."""

    dimension: str
    deterministic: list[Diff] = Field(default_factory=list)
    hypotheses: list[Diff] = Field(default_factory=list)


class Comparison(BaseModel):
    """A counterfactual comparison matrix with provenance (SRS REQ-063/066)."""

    baseline_commit_id: str
    intervention_id: str
    preserved_variable_ids: list[str] = Field(default_factory=list)
    rows: list[ComparisonRow] = Field(default_factory=list)
    unresolved_constraints: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord
