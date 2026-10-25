"""Tests for the Pydantic boundary contracts and provenance builder."""

import pytest

from nw_engine.contracts import (
    ActorRole,
    AuthorityState,
    Context,
    Mode,
    Origin,
    Proposal,
    ProposalState,
    Request,
    Response,
    StateObject,
)
from nw_engine.provenance import build_provenance


def test_context_defaults():
    c = Context()
    assert c.mode is Mode.COMPOSITION
    assert c.actor is ActorRole.NARRATIVE_DESIGNER
    assert c.commit_id is None


def test_state_object_mass_non_negative():
    with pytest.raises(ValueError):
        StateObject(id="b1", kind="actor", mass=-1.0)


def test_proposal_roundtrips_json():
    p = Proposal(id="p1", state=ProposalState.DRAFT, payload={"x": 1})
    data = p.model_dump_json()
    again = Proposal.model_validate_json(data)
    assert again == p


def test_request_response_envelope():
    r = Request(op="propose", op_id="o1", payload={"k": "v"})
    assert r.context.mode is Mode.COMPOSITION
    resp = Response(op_id="o1", ok=True, result={"done": True})
    assert resp.ok and resp.error is None


def test_build_provenance_sets_reproducibility():
    det = build_provenance(
        origin=Origin.DETERMINISTIC_RULE,
        actor=ActorRole.NARRATIVE_DESIGNER,
        authority=AuthorityState.ALLOWED,
        decision="accepted",
    )
    assert det.reproducibility == "replayable"

    human = build_provenance(
        origin=Origin.HUMAN,
        actor=ActorRole.NARRATIVE_DESIGNER,
        authority=AuthorityState.ALLOWED,
        decision="accepted",
    )
    assert human.reproducibility == "auditable"


def test_model_proposal_requires_metadata():
    with pytest.raises(ValueError):
        build_provenance(
            origin=Origin.MODEL_PROPOSAL,
            actor=ActorRole.AI_SERVICE,
            authority=AuthorityState.APPROVAL_REQUIRED,
            decision="proposed",
        )
    ok = build_provenance(
        origin=Origin.MODEL_PROPOSAL,
        actor=ActorRole.AI_SERVICE,
        authority=AuthorityState.APPROVAL_REQUIRED,
        decision="proposed",
        model_metadata={"provider": "test", "fingerprint": "abc"},
    )
    assert ok.reproducibility == "approximable"
