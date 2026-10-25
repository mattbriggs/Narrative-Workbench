"""Hard invariants and soft-goal scoring.

Each hard-invariant category from SRS SS8.3 is a small, deterministic check over
a validation payload. The engine aggregates failures and passes soft goals
through unchanged. A payload names only the facets relevant to the change; a
check fires only when its facet is present.

:caller contract: build the payload from the proposal delta and the minimal
    world slice (SRS REQ-130 step 2). The engine does not read the graph; the
    caller supplies the slice so validation stays pure and reproducible.
:return value: a :class:`ValidationResult`. ``passed`` is true only when there
    are no hard failures. Soft goals never affect ``passed`` (SRS REQ-079).
"""

from __future__ import annotations

from typing import Any

from nw_engine.contracts.models import HardFailure, SoftGoal, ValidationResult
from nw_engine.contracts.models import Mode

VALIDATOR_VERSION = "0.1.0"


def _check_knowledge(payload: dict[str, Any]) -> list[HardFailure]:
    """An actor cannot act on a proposition before acquiring or inferring it."""

    failures: list[HardFailure] = []
    known: dict[str, list[str]] = payload.get("knowledge", {})
    for req in payload.get("knowledge_requirements", []):
        actor = req["actor_id"]
        prop = req["proposition"]
        has = prop in known.get(actor, [])
        inferred = bool(req.get("inference_path"))
        if not has and not inferred:
            failures.append(
                HardFailure(
                    rule="knowledge",
                    scope=actor,
                    explanation=f"{actor} acts on {prop!r} before acquiring or inferring it",
                    alternatives=["disclose the proposition first", "add an inference path"],
                )
            )
    return failures


def _check_location_time(payload: dict[str, Any]) -> list[HardFailure]:
    """An object cannot occupy incompatible places at the same story time."""

    failures: list[HardFailure] = []
    seen: dict[tuple[str, int], str] = {}
    for p in payload.get("placements", []):
        key = (p["object_id"], p["story_time"])
        place = p["place"]
        if key in seen and seen[key] != place:
            failures.append(
                HardFailure(
                    rule="location_time",
                    scope=p["object_id"],
                    explanation=(
                        f"{p['object_id']} is in {seen[key]!r} and {place!r} at t={p['story_time']}"
                    ),
                    alternatives=["add a movement transition", "split the story time"],
                )
            )
        else:
            seen[key] = place
    return failures


def _check_disclosure(payload: dict[str, Any]) -> list[HardFailure]:
    """A concealed fact cannot become public without a mechanism."""

    failures: list[HardFailure] = []
    for d in payload.get("disclosures", []):
        if d.get("becomes_public") and not d.get("mechanism"):
            failures.append(
                HardFailure(
                    rule="disclosure",
                    scope=str(d.get("fact")),
                    explanation=f"concealed fact {d.get('fact')!r} becomes public with no mechanism",
                    alternatives=["add a disclosure event"],
                )
            )
    return failures


def _check_discourse(payload: dict[str, Any]) -> list[HardFailure]:
    """Point of view and narrative time must follow the active contract."""

    failures: list[HardFailure] = []
    d = payload.get("discourse")
    if d:
        pov_ok = d.get("pov") == d.get("contract_pov")
        time_ok = d.get("narrative_time") == d.get("contract_time")
        if (not pov_ok or not time_ok) and not d.get("operator_applied"):
            failures.append(
                HardFailure(
                    rule="discourse",
                    scope="discourse",
                    explanation="point of view or narrative time departs from the active contract",
                    alternatives=["apply a formal transition (operator)"],
                )
            )
    return failures


def _check_source_integrity(payload: dict[str, Any]) -> list[HardFailure]:
    """Evidence anchors must resolve to the frozen source edition."""

    failures: list[HardFailure] = []
    for a in payload.get("required_anchor_resolution", []):
        if not a.get("resolves", True):
            failures.append(
                HardFailure(
                    rule="source_integrity",
                    scope=str(a.get("anchor_id")),
                    explanation=f"evidence anchor {a.get('anchor_id')!r} does not resolve",
                    alternatives=["realign the anchor"],
                )
            )
    return failures


def _check_mode_authority(payload: dict[str, Any]) -> list[HardFailure]:
    """A laboratory branch cannot overwrite imported source or canonical state."""

    failures: list[HardFailure] = []
    ma = payload.get("mode_authority")
    if ma and ma.get("action") == "overwrite":
        target = ma.get("target")
        mode = ma.get("mode")
        if target in ("frozen_source", "canonical") and mode in (
            Mode.COUNTERFACTUAL.value,
            Mode.CRITICISM.value,
        ):
            failures.append(
                HardFailure(
                    rule="mode_authority",
                    scope=str(target),
                    explanation=f"{mode} mode may not overwrite {target}",
                    alternatives=["fork into an owned work", "export the result"],
                )
            )
    return failures


def _soft_motivation(payload: dict[str, Any]) -> list[SoftGoal]:
    """Motivation vanishing without cause is a review warning, not a hard fail."""

    goals: list[SoftGoal] = []
    for m in payload.get("removed_motivations", []):
        if not m.get("cause") and not m.get("model_change"):
            goals.append(
                SoftGoal(
                    name="motivation_continuity",
                    score=0.0,
                    rationale=(
                        f"{m.get('actor_id')} loses motivation {m.get('motivation')!r} "
                        "without an accepted cause or model change"
                    ),
                )
            )
    return goals


# All hard-invariant checks, in deterministic order.
_HARD_CHECKS = (
    _check_knowledge,
    _check_location_time,
    _check_disclosure,
    _check_discourse,
    _check_source_integrity,
    _check_mode_authority,
)


class ValidationEngine:
    """Runs hard invariants and collects soft goals.

    The engine is stateless; construct once and reuse. It may reject a change
    but never ranks literary merit (SRS SS2.3).
    """

    def validate(self, payload: dict[str, Any]) -> ValidationResult:
        """Validate a change payload.

        :param payload: the proposal delta plus minimal world slice.
        :returns: a :class:`ValidationResult` with hard failures, soft goals,
            and uncertainty. ``passed`` is true only when no hard check fails.
        """

        hard: list[HardFailure] = []
        for check in _HARD_CHECKS:
            hard.extend(check(payload))

        soft: list[SoftGoal] = list(_soft_motivation(payload))
        for g in payload.get("soft_goals", []):
            soft.append(SoftGoal(name=g["name"], score=float(g["score"]), rationale=g.get("rationale", "")))

        return ValidationResult(
            passed=not hard,
            hard_failures=hard,
            soft_goals=soft,
            uncertainty=payload.get("uncertainty"),
            validator_version=VALIDATOR_VERSION,
        )
