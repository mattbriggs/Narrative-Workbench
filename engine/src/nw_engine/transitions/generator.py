"""Candidate trajectory generation (SRS REQ-040..046, REQ-130).

The generator asks the AI gateway for candidate trajectories, validates each one
deterministically, scores soft goals separately from validity, and preserves
every candidate (divergent alternatives are not collapsed, SRS REQ-079).
Forbidding a transition produces a constraint (**gate**) proposal and preserves
the current candidate (SRS REQ-046).
"""

from __future__ import annotations

from typing import Optional

from nw_engine.ai import AIGateway
from nw_engine.contracts.models import (
    AuthorityState,
    Candidate,
    Origin,
    Proposal,
)
from nw_engine.validation import ValidationEngine


class TrajectoryGenerator:
    """Generates and validates candidate trajectories.

    :param gateway: the AI gateway that proposes candidates (advisory).
    :param validator: the deterministic validation engine.
    """

    def __init__(self, gateway: AIGateway, validator: Optional[ValidationEngine] = None) -> None:
        self._gateway = gateway
        self._validator = validator or ValidationEngine()

    def generate(self, target: str, payloads: Optional[dict[str, dict]] = None) -> list[Candidate]:
        """Produce validated candidates for a target condition (**sink**).

        :param target: the target condition the trajectories move toward.
        :param payloads: optional map of candidate id -> validation payload
            (the minimal world slice for that candidate). Missing payloads
            validate as empty (vacuously passing).
        :returns: all candidates with a :class:`ValidationResult` attached;
            invalid candidates are kept, not dropped (SRS REQ-079).
        """

        payloads = payloads or {}
        candidates = self._gateway.propose_candidates(target)
        for cand in candidates:
            cand.validation = self._validator.validate(payloads.get(cand.id, {}))
        return candidates

    @staticmethod
    def valid_candidates(candidates: list[Candidate]) -> list[Candidate]:
        """Return only candidates whose hard checks passed (helper for UI)."""

        return [c for c in candidates if c.validation and c.validation.passed]

    @staticmethod
    def forbid(candidate: Candidate, transition_id: str) -> Proposal:
        """Create a constraint (**gate**) proposal forbidding a transition.

        The candidate itself is unchanged and remains available (SRS REQ-046).

        :returns: a draft constraint :class:`Proposal`.
        """

        return Proposal(
            id=f"gate-{candidate.id}-{transition_id}",
            origin=Origin.HUMAN,
            payload={"forbid_transition": transition_id, "within_candidate": candidate.id},
            authority_required=AuthorityState.APPROVAL_REQUIRED,
        )
