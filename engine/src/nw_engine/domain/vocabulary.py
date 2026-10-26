"""Fixed narrative vocabulary.

Defines the state-field terms, typed relationship vocabulary, transition
classes, and assertion levels from the governing spec and architecture. These
names are fixed by ``CLAUDE.md`` and MUST NOT be renamed, pluralized into new
terms, or given synonyms.

:caller contract: Import the enums and the glossary; do not redefine the member
    values. ``ghost`` is intentionally present but undefined (SRS OQ-12); using
    it as a feature is prohibited until an owner defines it.
:extension points: ``RelationshipType`` and ``TransitionClass`` are closed by
    the architecture (NW ADD v1.1 Tables 8-10); frameworks extend behavior
    through validators, not by adding edge types here.
"""

from __future__ import annotations

from enum import Enum


class StateFieldTerm(str, Enum):
    """The fixed state-field vocabulary (``CLAUDE.md`` SS "State-field vocabulary").

    Each term maps to an architecture entity; the mapping is recorded in
    :data:`STATE_FIELD_GLOSSARY`.
    """

    BODY = "body"
    IMPULSE = "impulse"
    BOUNDARY = "boundary"
    SINK = "sink"
    GATE = "gate"
    PIN = "pin"
    GHOST = "ghost"


#: Human-readable meaning for each state-field term. ``ghost`` is undefined on
#: purpose (SRS OQ-12); its value names that fact rather than inventing one.
STATE_FIELD_GLOSSARY: dict[StateFieldTerm, str] = {
    StateFieldTerm.BODY: "Narrative object; its size is its mass (resistance).",
    StateFieldTerm.IMPULSE: "A change applied to the field, numbered in order.",
    StateFieldTerm.BOUNDARY: "The edge of the active model.",
    StateFieldTerm.SINK: "A terminal or attracting state.",
    StateFieldTerm.GATE: "A constraint (friction).",
    StateFieldTerm.PIN: "An evidence pin that ties a claim to its source.",
    StateFieldTerm.GHOST: "Not yet defined in the design sources (open question OQ-12).",
}


class RelationshipType(str, Enum):
    """Typed edge vocabulary (NW ADD v1.1 Table 8, SRS REQ-013)."""

    PART_OF = "PART_OF"
    PRECEDES = "PRECEDES"
    PRESENTED_BEFORE = "PRESENTED_BEFORE"
    CAUSES = "CAUSES"
    REVEALS = "REVEALS"
    REINTERPRETS = "REINTERPRETS"
    REALIZES = "REALIZES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"


#: The constraint each edge type carries. Used by the validator to reject edges
#: that violate their declared semantics (SRS REQ-013).
_RELATIONSHIP_CONSTRAINTS: dict[RelationshipType, str] = {
    RelationshipType.PART_OF: "Organizational containment; must not imply causality.",
    RelationshipType.PRECEDES: "Order in story time; distinct from presentation order.",
    RelationshipType.PRESENTED_BEFORE: "Order encountered by the reader; may cross story time.",
    RelationshipType.CAUSES: "Requires an explicit causal claim and scope.",
    RelationshipType.REVEALS: "Names the recipient model and disclosed proposition.",
    RelationshipType.REINTERPRETS: "Must not alter the earlier event record.",
    RelationshipType.REALIZES: "Many realizations may express the same transition.",
    RelationshipType.SUPPORTS: "Does not imply the claim is uniquely entailed.",
    RelationshipType.CONTRADICTS: "Contradiction may be deliberate and need not be repaired.",
    RelationshipType.DERIVED_FROM: "Must resolve to a specific source version.",
}


def relationship_constraint(rel: RelationshipType) -> str:
    """Return the declared constraint text for an edge type.

    :param rel: a :class:`RelationshipType` member.
    :returns: the constraint sentence used in validation messages.
    """

    return _RELATIONSHIP_CONSTRAINTS[rel]


class TransitionClass(str, Enum):
    """Transition classes (NW ADD v1.1 Table 10)."""

    CAUSAL = "causal"
    EPISTEMIC = "epistemic"
    AFFECTIVE = "affective"
    STRUCTURAL = "structural"
    FORMAL = "formal"
    READER_MODEL = "reader_model"
    ONTOLOGICAL = "ontological"


class AssertionLevel(str, Enum):
    """The three evidence-to-interpretation levels (SRS REQ-054)."""

    OBSERVATION = "observation"
    FINDING = "finding"
    CLAIM = "claim"
