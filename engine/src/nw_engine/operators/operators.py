"""Formal operator definitions and application.

Applying an operator adds its declared formal relation between units in the
graph. The engine refuses to let a formal operator assert a diegetic ``CAUSES``
edge, so juxtaposition is never mistaken for in-world causality (SRS REQ-035).
Operators that deliberately preserve ambiguity are classified as intentional
irresolution, not accidental inconsistency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from nw_engine.contracts.models import ModelTransition
from nw_engine.domain.vocabulary import RelationshipType
from nw_engine.errors import GraphConstraintError
from nw_engine.graph import GraphKernel


class OperatorName(str, Enum):
    """The initial formal operator vocabulary (NW ADD v1.1 Table 12)."""

    INTERRUPT = "INTERRUPT"
    RECURSE = "RECURSE"
    REFRACT = "REFRACT"
    COLLAGE = "COLLAGE"
    SPIRAL = "SPIRAL"
    WITHHOLD = "WITHHOLD"
    REINTERPRET = "REINTERPRET"
    TRANSPOSE = "TRANSPOSE"


@dataclass(frozen=True)
class FormalOperator:
    """A versioned formal operator definition.

    :ivar name: the :class:`OperatorName`.
    :ivar target_scale: the unit scale it acts on (e.g. ``"scene"``, ``"work"``).
    :ivar relation: the formal relation it produces; never ``CAUSES``.
    :ivar reversible: whether the transformation can be undone.
    :ivar preserves_ambiguity: whether it deliberately preserves irresolution.
    """

    name: OperatorName
    target_scale: str
    relation: RelationshipType
    reversible: bool
    preserves_ambiguity: bool

    def apply(self, kernel: GraphKernel, src: str, dst: str, **attrs: object) -> None:
        """Apply the operator between two units, adding its formal relation.

        :raises GraphConstraintError: if the operator's relation is ``CAUSES``
            (a formal operator may not assert diegetic cause, SRS REQ-035), or
            if the kernel rejects the edge.
        """

        if self.relation is RelationshipType.CAUSES:
            raise GraphConstraintError(
                f"formal operator {self.name.value} may not assert diegetic CAUSES",
                scope=f"{src}->{dst}",
            )
        kernel.add_edge(src, dst, self.relation, **attrs)

    def classify_inconsistency(self, has_contradiction: bool) -> str:
        """Classify a detected contradiction under this operator.

        :returns: ``"intentional"`` when the operator preserves ambiguity and a
            contradiction is present; ``"accidental"`` when a contradiction is
            present without that license; ``"none"`` when there is no
            contradiction (SRS REQ-035).
        """

        if not has_contradiction:
            return "none"
        return "intentional" if self.preserves_ambiguity else "accidental"


#: The eight default operators with their declared properties.
DEFAULT_OPERATORS: dict[OperatorName, FormalOperator] = {
    OperatorName.INTERRUPT: FormalOperator(OperatorName.INTERRUPT, "scene", RelationshipType.PRESENTED_BEFORE, True, False),
    OperatorName.RECURSE: FormalOperator(OperatorName.RECURSE, "unit", RelationshipType.PART_OF, True, False),
    OperatorName.REFRACT: FormalOperator(OperatorName.REFRACT, "scene", RelationshipType.PRESENTED_BEFORE, True, True),
    OperatorName.COLLAGE: FormalOperator(OperatorName.COLLAGE, "work", RelationshipType.PART_OF, False, True),
    OperatorName.SPIRAL: FormalOperator(OperatorName.SPIRAL, "motif", RelationshipType.PRESENTED_BEFORE, False, True),
    OperatorName.WITHHOLD: FormalOperator(OperatorName.WITHHOLD, "discourse", RelationshipType.REVEALS, True, True),
    OperatorName.REINTERPRET: FormalOperator(OperatorName.REINTERPRET, "work", RelationshipType.REINTERPRETS, False, False),
    OperatorName.TRANSPOSE: FormalOperator(OperatorName.TRANSPOSE, "work", RelationshipType.REALIZES, True, False),
}


class OperatorLibrary:
    """Holds configured formal operators (plugin-style, SRS NFR-050)."""

    def __init__(self) -> None:
        self._ops: dict[OperatorName, FormalOperator] = dict(DEFAULT_OPERATORS)

    def get(self, name: OperatorName) -> FormalOperator:
        """Return a configured operator by name."""

        return self._ops[name]

    def register(self, operator: FormalOperator) -> None:
        """Register or replace an operator definition (author-configurable)."""

        self._ops[operator.name] = operator


def reader_model_transition(
    trigger: str, reinterpreted_events: list[str], new_affordances: list[str], is_epiphany: bool = False
) -> ModelTransition:
    """Build a reader-model transition (SRS REQ-015, experimental form).

    The transition changes the reader model's expectations/reinterpretations
    without any diegetic cause edge; it names the events it reclassifies but
    does not mutate them.

    :returns: a :class:`ModelTransition` whose ``affected_model`` is ``"reader"``.
    """

    return ModelTransition(
        id=f"rmt-{trigger}",
        trigger=trigger,
        affected_model="reader",
        reinterpreted_events=list(reinterpreted_events),
        new_affordances=list(new_affordances),
        is_epiphany=is_epiphany,
    )
