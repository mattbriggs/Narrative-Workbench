"""Tests for interpretive assertions and comparison (SRS SS3.6)."""

import pytest

from nw_engine.contracts.models import AssertionLevel, EvidenceAnchor, Interpretation, Origin
from nw_engine.criticism import InterpretationStore
from nw_engine.errors import HardInvariantError
from nw_engine.provenance import AnchorStore


@pytest.fixture()
def anchors():
    s = AnchorStore()
    s.freeze_edition("ed1", "fp")
    s.add_anchor(EvidenceAnchor(id="a1", source_edition_id="ed1", region="p1", fingerprint="fp"))
    s.add_anchor(EvidenceAnchor(id="a2", source_edition_id="ed1", region="p2", fingerprint="fp"))
    return s


def test_accept_requires_resolved_evidence(anchors):
    store = InterpretationStore(anchors)
    store.add(Interpretation(id="c1", level=AssertionLevel.CLAIM, text="irony", supporting_anchors=["a1"], branch_id="reading1"))
    accepted = store.accept("c1")
    assert accepted.accepted is True
    assert accepted.level is AssertionLevel.CLAIM  # stays interpretive, not source


def test_accept_without_evidence_is_rejected(anchors):
    store = InterpretationStore(anchors)
    store.add(Interpretation(id="c2", level=AssertionLevel.CLAIM, text="unsupported", supporting_anchors=[]))
    with pytest.raises(HardInvariantError):
        store.accept("c2")


def test_broken_anchor_blocks_publication(anchors):
    store = InterpretationStore(anchors)
    store.add(Interpretation(id="c3", level=AssertionLevel.FINDING, text="pattern", supporting_anchors=["a1"]))
    assert store.publication_status("c3") == "ready"
    anchors.break_anchor("a1")
    assert store.publication_status("c3") == "blocked"
    with pytest.raises(HardInvariantError):
        store.accept("c3")


def test_compare_competing_lenses(anchors):
    store = InterpretationStore(anchors)
    store.add(Interpretation(id="c4", level=AssertionLevel.CLAIM, text="loyalty reading", lens="structural", supporting_anchors=["a1"]))
    store.add(Interpretation(id="c5", level=AssertionLevel.CLAIM, text="suspicion reading", lens="modal", supporting_anchors=["a1", "a2"], contradicting_anchors=["a2"]))
    cmp = store.compare("structural", "modal")
    assert cmp.shared_anchors == ["a1"]
    assert "loyalty reading" in cmp.a_only_claims
    assert "suspicion reading" in cmp.b_only_claims
    assert any("a2" in u for u in cmp.unresolved_conflicts)
