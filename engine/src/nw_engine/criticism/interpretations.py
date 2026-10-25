"""Interpretive assertions and competing-model comparison.

An interpretation is an Observation, Finding, or Claim on a named interpretive
branch. Acceptance requires at least one resolved supporting anchor (pin), and
never converts the assertion into a source fact. Several lenses may coexist and
be compared without rewriting source text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nw_engine.contracts.models import AssertionLevel, Interpretation
from nw_engine.errors import HardInvariantError
from nw_engine.provenance import AnchorStore


@dataclass
class ModelComparison:
    """The result of comparing two interpretive models (SRS REQ-056)."""

    lens_a: str
    lens_b: str
    shared_anchors: list[str] = field(default_factory=list)
    unresolved_conflicts: list[str] = field(default_factory=list)
    a_only_claims: list[str] = field(default_factory=list)
    b_only_claims: list[str] = field(default_factory=list)


class InterpretationStore:
    """Holds interpretations and enforces evidence-backed acceptance.

    :param anchors: the shared :class:`AnchorStore` used to resolve pins.
    """

    def __init__(self, anchors: AnchorStore) -> None:
        self._anchors = anchors
        self._items: dict[str, Interpretation] = {}

    def add(self, interp: Interpretation) -> None:
        """Add an interpretation (proposed, not yet accepted)."""

        self._items[interp.id] = interp

    def accept(self, interp_id: str) -> Interpretation:
        """Accept an interpretation after checking its evidence.

        :raises HardInvariantError: if no supporting anchor resolves (an
            observation or claim needs evidence, SRS REQ-053).
        :returns: the accepted interpretation; it keeps its level and branch and
            is never relabeled as a source fact (SRS REQ-058).
        """

        interp = self._items[interp_id]
        resolved = [a for a in interp.supporting_anchors if self._anchors.resolves(a)]
        if not resolved:
            raise HardInvariantError(
                f"interpretation {interp_id} has no resolved supporting evidence",
                scope=interp_id,
            )
        accepted = interp.model_copy(update={"accepted": True})
        self._items[interp_id] = accepted
        return accepted

    def publication_status(self, interp_id: str) -> str:
        """Return ``"ready"`` or ``"blocked"`` based on anchor resolution."""

        interp = self._items[interp_id]
        return self._anchors.publication_status(interp.supporting_anchors)

    def by_lens(self, lens: str) -> list[Interpretation]:
        """Return interpretations recorded under a lens, ordered by id."""

        return sorted((i for i in self._items.values() if i.lens == lens), key=lambda i: i.id)

    def compare(self, lens_a: str, lens_b: str) -> ModelComparison:
        """Compare two lenses over the same source (SRS REQ-056).

        :returns: a :class:`ModelComparison` naming shared anchors, each lens's
            unique claims, and unresolved contradictions.
        """

        a = self.by_lens(lens_a)
        b = self.by_lens(lens_b)
        a_anchors = {anc for i in a for anc in i.supporting_anchors}
        b_anchors = {anc for i in b for anc in i.supporting_anchors}
        a_claims = {i.text for i in a if i.level is AssertionLevel.CLAIM}
        b_claims = {i.text for i in b if i.level is AssertionLevel.CLAIM}
        unresolved = [
            f"{i.text} contradicted by {anc}"
            for i in a + b
            for anc in i.contradicting_anchors
        ]
        return ModelComparison(
            lens_a=lens_a,
            lens_b=lens_b,
            shared_anchors=sorted(a_anchors & b_anchors),
            unresolved_conflicts=sorted(unresolved),
            a_only_claims=sorted(a_claims - b_claims),
            b_only_claims=sorted(b_claims - a_claims),
        )
