"""Tests for the proposal-only AI gateway (SRS SS3.10)."""

import pytest

from nw_engine.ai import AIGateway, ReferencePlanner
from nw_engine.contracts.models import Origin
from nw_engine.errors import AuthorityDeniedError
from nw_engine.sources import SourceIngestor


@pytest.fixture()
def gateway():
    return AIGateway(ReferencePlanner(), provider="reference", model="det-0")


def test_extraction_returns_proposals_only(gateway):
    anchors = SourceIngestor().ingest("ed1", "A letter arrives.\n\nB grows suspicious.")
    proposals = gateway.extract_observations(anchors)
    assert len(proposals) == 2
    for p in proposals:
        assert p.origin is Origin.MODEL_PROPOSAL
        assert p.model_metadata["provider"] == "reference"
        # Advisory: the wrapped interpretation is not accepted.
        assert p.payload["interpretation"]["accepted"] is False


def test_candidates_are_advisory(gateway):
    candidates = gateway.propose_candidates("reconcile the letter")
    assert [c.label for c in candidates] == ["Trajectory A", "Trajectory B"]
    assert candidates[0].validation is None  # not yet validated


@pytest.mark.parametrize(
    "action",
    ["overwrite_source", "overwrite_history", "approve_own_proposal", "change_policy", "claim_reader_response", "imitate_living_author"],
)
def test_prohibited_authority_is_blocked(action):
    with pytest.raises(AuthorityDeniedError):
        AIGateway.guard(action)


def test_permitted_action_passes_guard():
    AIGateway.guard("extract")  # no raise


def test_metadata_fingerprint(gateway):
    md = gateway.metadata()
    assert md["fingerprint"] == "reference:det-0"
