"""Counterfactual comparison matrix.

Builds a matrix across the seven dimensions, separating deterministic
consequences from generated hypotheses and always carrying provenance
(SRS REQ-063/066). The reader-model dimension is labeled "Intended response"
and never asserts an empirical effect (SRS REQ-065).
"""

from __future__ import annotations

from nw_engine.contracts.models import (
    ActorRole,
    AuthorityState,
    Comparison,
    ComparisonRow,
    Diff,
    Origin,
)
from nw_engine.provenance import build_provenance

#: The seven comparison dimensions, in order (SRS REQ-063). "Reader model" is
#: presented as intended, not measured.
DIMENSIONS = (
    "World",
    "Epistemic",
    "Affective",
    "Structural",
    "Formal",
    "Reader model",
    "Provenance",
)

#: Labels every changed value must use (SRS REQ-064).
_VALID_LABELS = {"Added", "Removed", "Changed", "Invariant"}


class ComparisonBuilder:
    """Assembles a counterfactual comparison matrix.

    :param baseline_commit_id: the immutable baseline.
    :param intervention_id: the declared intervention.
    :param preserved_variable_ids: the controls kept fixed.
    """

    def __init__(
        self,
        baseline_commit_id: str,
        intervention_id: str,
        preserved_variable_ids: list[str] | None = None,
    ) -> None:
        self._baseline = baseline_commit_id
        self._intervention = intervention_id
        self._preserved = list(preserved_variable_ids or [])
        self._rows: dict[str, ComparisonRow] = {d: ComparisonRow(dimension=d) for d in DIMENSIONS}
        self._unresolved: list[str] = []

    def add_deterministic(self, dimension: str, diff: Diff) -> None:
        """Record a deterministic consequence on a dimension.

        :raises ValueError: for an unknown dimension or an unlabeled diff.
        """

        self._require(dimension, diff)
        self._rows[dimension].deterministic.append(diff)

    def add_hypothesis(self, dimension: str, diff: Diff) -> None:
        """Record a generated hypothesis on a dimension (kept distinct from fact)."""

        self._require(dimension, diff)
        self._rows[dimension].hypotheses.append(diff)

    def add_unresolved(self, constraint: str) -> None:
        """Record an unmet control or unresolved constraint (SRS REQ-066)."""

        self._unresolved.append(constraint)

    def build(self) -> Comparison:
        """Return the assembled :class:`Comparison` with provenance always set."""

        prov = build_provenance(
            origin=Origin.DERIVED_PROJECTION,
            actor=ActorRole.RESEARCHER,
            authority=AuthorityState.ALLOWED,
            decision="counterfactual comparison",
            inputs={
                "baseline": self._baseline,
                "intervention": self._intervention,
                "preserved": self._preserved,
            },
        )
        return Comparison(
            baseline_commit_id=self._baseline,
            intervention_id=self._intervention,
            preserved_variable_ids=self._preserved,
            rows=[self._rows[d] for d in DIMENSIONS],
            unresolved_constraints=list(self._unresolved),
            provenance=prov,
        )

    def _require(self, dimension: str, diff: Diff) -> None:
        if dimension not in self._rows:
            raise ValueError(f"unknown comparison dimension {dimension!r}")
        if diff.label not in _VALID_LABELS:
            raise ValueError(f"diff label must be one of {sorted(_VALID_LABELS)}")
        if dimension == "Reader model" and "measured" in diff.subject.lower():
            raise ValueError("reader model dimension must not assert measured reader response")
