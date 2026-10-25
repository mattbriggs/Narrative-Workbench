"""Prose reconciliation (SRS REQ-047/048).

Prose realization follows an accepted commit. When a prose edit introduces an
assertion absent from the model, the reconciler raises a reconciliation
proposal that lets the author choose whether the language or the model is
authoritative. It never mutates the model silently (SRS REQ-048, risk
"silent state invention").
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReconciliationProposal:
    """A discrepancy between edited prose and the accepted model.

    :ivar assertion: the assertion found in prose but absent from the model.
    :ivar realization_id: the prose realization that introduced it.
    :ivar resolution: ``None`` until the author chooses ``"language"`` or
        ``"model"`` authority.
    """

    assertion: str
    realization_id: str
    resolution: str | None = None


class ProseReconciler:
    """Detects and resolves prose/model discrepancies."""

    def detect(
        self, model_assertions: set[str], prose_assertions: list[str], realization_id: str
    ) -> list[ReconciliationProposal]:
        """Return a proposal per prose assertion missing from the model.

        :param model_assertions: assertions already in the accepted model.
        :param prose_assertions: assertions implied by the edited prose.
        :param realization_id: the prose realization under edit.
        :returns: one :class:`ReconciliationProposal` per new assertion, in
            document order, de-duplicated.
        """

        seen: set[str] = set()
        proposals: list[ReconciliationProposal] = []
        for assertion in prose_assertions:
            if assertion not in model_assertions and assertion not in seen:
                seen.add(assertion)
                proposals.append(ReconciliationProposal(assertion=assertion, realization_id=realization_id))
        return proposals

    @staticmethod
    def resolve(proposal: ReconciliationProposal, choice: str) -> ReconciliationProposal:
        """Record the author's authority choice.

        :param choice: ``"language"`` (accept prose into the model) or
            ``"model"`` (treat the prose as a defect to revise).
        :raises ValueError: for any other choice.
        """

        if choice not in ("language", "model"):
            raise ValueError("reconciliation choice must be 'language' or 'model'")
        proposal.resolution = choice
        return proposal
