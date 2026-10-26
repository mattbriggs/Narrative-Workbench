"""Tests for evidence anchors and the publication gate (SRS REQ-051, REQ-057)."""

import pytest

from nw_engine.contracts.models import EvidenceAnchor
from nw_engine.errors import AnchorBrokenError, SourceImmutableError
from nw_engine.provenance import AnchorStore


@pytest.fixture()
def store():
    s = AnchorStore()
    s.freeze_edition("ed1", "fp-abc")
    s.add_anchor(EvidenceAnchor(id="a1", source_edition_id="ed1", region="p12", fingerprint="fp-abc"))
    return s


def test_anchor_resolves(store):
    assert store.resolves("a1") is True
    assert store.publication_status(["a1"]) == "ready"


def test_unknown_anchor_does_not_resolve(store):
    assert store.resolves("nope") is False


def test_anchor_against_unknown_edition_is_broken(store):
    with pytest.raises(AnchorBrokenError):
        store.add_anchor(EvidenceAnchor(id="a2", source_edition_id="edX", region="r", fingerprint="fp"))


def test_anchor_fingerprint_mismatch_is_broken(store):
    with pytest.raises(AnchorBrokenError):
        store.add_anchor(EvidenceAnchor(id="a3", source_edition_id="ed1", region="r", fingerprint="WRONG"))


def test_breaking_anchor_blocks_publication(store):
    store.break_anchor("a1")
    assert store.resolves("a1") is False
    assert store.publication_status(["a1"]) == "blocked"


def test_refreezing_with_different_fingerprint_is_rejected(store):
    with pytest.raises(SourceImmutableError):
        store.freeze_edition("ed1", "fp-different")
    # Idempotent re-freeze with the same fingerprint is fine.
    store.freeze_edition("ed1", "fp-abc")
