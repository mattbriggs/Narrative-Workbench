"""The proposal-only AI gateway.

The gateway wraps a :class:`Planner` (Strategy pattern) so a deterministic
reference planner can stand in for a probabilistic provider during tests and in
the cloud. Every output is a :class:`~nw_engine.contracts.models.Proposal` with
``origin = MODEL_PROPOSAL`` and attached model metadata; the gateway never
returns durable state. Prohibited authority is enforced up front
(SRS REQ-101..105).

:framework integration: real providers implement :class:`Planner`; the gateway
    is the only path from a provider into the system, so the mutation boundary
    and provenance capture always apply.
"""

from __future__ import annotations

from typing import Protocol

from nw_engine.contracts.models import (
    AssertionLevel,
    AuthorityState,
    Candidate,
    EvidenceAnchor,
    Interpretation,
    Origin,
    Proposal,
    Transition,
)
from nw_engine.errors import AuthorityDeniedError

#: Actions no model may perform (SRS REQ-101..105). Requesting one raises.
_PROHIBITED = {
    "overwrite_source",
    "overwrite_history",
    "approve_own_proposal",
    "change_policy",
    "claim_reader_response",
    "imitate_living_author",
}


class Planner(Protocol):
    """A provider of candidate narrative material.

    Implementations may be probabilistic; the gateway treats all output as
    advisory proposals.
    """

    def extract(self, spans: list[str]) -> list[str]:
        """Return candidate observation texts for the given source spans."""

    def plan(self, target: str) -> list[list[Transition]]:
        """Return candidate trajectories (each a list of transitions) for a target."""


class ReferencePlanner:
    """A deterministic planner used for tests and cloud runs.

    It derives stable, inspectable output from its inputs so proposals are
    reproducible (SRS NFR-031).
    """

    def extract(self, spans: list[str]) -> list[str]:
        """Return one observation per span, naming the span's first words."""

        return [f"observation: {s.strip().split(chr(10))[0][:40]}" for s in spans if s.strip()]

    def plan(self, target: str) -> list[list[Transition]]:
        """Return two deterministic candidate trajectories toward a target."""

        base = Transition(id="t-a1", order=1, description=f"approach {target} directly")
        alt = Transition(id="t-b1", order=1, description=f"approach {target} obliquely")
        return [[base], [alt]]


class AIGateway:
    """Normalizes provider access and enforces the AI boundary.

    :param planner: the strategy that produces candidate material.
    :param provider: provider id recorded in model metadata.
    :param model: model id recorded in model metadata.
    """

    def __init__(self, planner: Planner, provider: str = "reference", model: str = "det-0") -> None:
        self._planner = planner
        self._provider = provider
        self._model = model

    def metadata(self) -> dict[str, str]:
        """Return provider/model metadata attached to every proposal."""

        return {"provider": self._provider, "model": self._model, "fingerprint": f"{self._provider}:{self._model}"}

    @staticmethod
    def guard(action: str) -> None:
        """Raise if ``action`` is a prohibited model authority (SRS REQ-101..105).

        :raises AuthorityDeniedError: when the action is in the prohibited set.
        """

        if action in _PROHIBITED:
            raise AuthorityDeniedError(f"model may not {action}", scope="ai_boundary")

    def extract_observations(self, anchors: list[EvidenceAnchor]) -> list[Proposal]:
        """Produce observation proposals anchored to source spans (SRS REQ-052).

        Each proposal is advisory (not accepted) and carries model metadata and
        the supporting anchor id. A critic must accept it before any commit.
        """

        texts = self._planner.extract([a.region for a in anchors])
        proposals: list[Proposal] = []
        for i, text in enumerate(texts):
            anchor = anchors[i]
            interp = Interpretation(
                id=f"obs-{anchor.id}",
                level=AssertionLevel.OBSERVATION,
                text=text,
                proposer=Origin.MODEL_PROPOSAL,
                supporting_anchors=[anchor.id],
                accepted=False,
            )
            proposals.append(
                Proposal(
                    id=f"p-{interp.id}",
                    origin=Origin.MODEL_PROPOSAL,
                    payload={"interpretation": interp.model_dump()},
                    authority_required=AuthorityState.APPROVAL_REQUIRED,
                    model_metadata=self.metadata(),
                )
            )
        return proposals

    def propose_candidates(self, target: str) -> list[Candidate]:
        """Produce candidate trajectories for a composition target (SRS REQ-100).

        Candidates are advisory; validation and human acceptance follow.
        """

        trajectories = self._planner.plan(target)
        labels = ["A", "B", "C", "D"]
        candidates: list[Candidate] = []
        for i, transitions in enumerate(trajectories):
            candidates.append(
                Candidate(
                    id=f"cand-{labels[i] if i < len(labels) else i}",
                    label=f"Trajectory {labels[i] if i < len(labels) else i}",
                    transitions=transitions,
                )
            )
        return candidates
