"""Provenance record construction.

A provenance record captures the seven fields required by NW ADD v1.1 Table 16
(SRS REQ-097). Probabilistic origins MUST carry model metadata (SRS REQ-194).
"""

from __future__ import annotations

from typing import Any, Optional

from nw_engine.contracts.models import (
    ActorRole,
    AuthorityState,
    Origin,
    ProvenanceRecord,
)


def build_provenance(
    *,
    origin: Origin,
    actor: ActorRole,
    authority: AuthorityState,
    decision: str,
    inputs: Optional[dict[str, Any]] = None,
    alternatives: Optional[list[str]] = None,
    model_metadata: Optional[dict[str, Any]] = None,
) -> ProvenanceRecord:
    """Build a complete provenance record.

    :param origin: where the change came from.
    :param actor: the role responsible.
    :param authority: the authority decision bound to the change.
    :param decision: the accepted delta, rejection reason, or status.
    :param inputs: source anchors, prior states, framework/policy versions.
    :param alternatives: candidate transitions considered but not accepted.
    :param model_metadata: provider/model/config/fingerprint for probabilistic
        output; required when ``origin`` is :attr:`Origin.MODEL_PROPOSAL`.
    :returns: a :class:`ProvenanceRecord` with a derived reproducibility status.
    :raises ValueError: if a model proposal omits model metadata (SRS REQ-194).
    """

    if origin is Origin.MODEL_PROPOSAL and not model_metadata:
        raise ValueError("model proposals must carry model metadata (REQ-194)")
    reproducibility = "replayable" if origin in (Origin.DETERMINISTIC_RULE, Origin.DERIVED_PROJECTION) else (
        "approximable" if origin is Origin.MODEL_PROPOSAL else "auditable"
    )
    return ProvenanceRecord(
        origin=origin,
        actor=actor,
        authority=authority,
        inputs=inputs or {},
        decision=decision,
        alternatives=alternatives or [],
        model_metadata=model_metadata,
        reproducibility=reproducibility,
    )
