"""Tests for candidate generation and prose reconciliation (SRS SS3.5)."""

import pytest

from nw_engine.ai import AIGateway, ReferencePlanner
from nw_engine.transitions import ProseReconciler, TrajectoryGenerator


@pytest.fixture()
def generator():
    return TrajectoryGenerator(AIGateway(ReferencePlanner()))


def test_generate_validates_each_candidate(generator):
    cands = generator.generate("reconcile the letter")
    assert len(cands) == 2
    assert all(c.validation is not None for c in cands)
    assert all(c.validation.passed for c in cands)  # empty payloads pass


def test_invalid_candidate_is_kept_not_dropped(generator):
    payloads = {
        "cand-A": {"disclosures": [{"fact": "letter", "becomes_public": True}]},  # hard fail
        "cand-B": {},
    }
    cands = generator.generate("x", payloads)
    assert len(cands) == 2  # divergent candidates preserved (REQ-079)
    valid = TrajectoryGenerator.valid_candidates(cands)
    assert [c.id for c in valid] == ["cand-B"]


def test_forbid_creates_gate_and_preserves_candidate(generator):
    cands = generator.generate("x")
    gate = TrajectoryGenerator.forbid(cands[0], "t-a1")
    assert gate.payload["forbid_transition"] == "t-a1"
    assert gate.payload["within_candidate"] == cands[0].id
    # Candidate itself is unchanged and still present.
    assert cands[0].id == "cand-A"


def test_reconcile_detects_new_prose_assertions():
    rec = ProseReconciler()
    proposals = rec.detect(
        model_assertions={"B is suspicious"},
        prose_assertions=["B is suspicious", "B owns a revolver", "B owns a revolver"],
        realization_id="P0082",
    )
    assert [p.assertion for p in proposals] == ["B owns a revolver"]  # de-duplicated, only-new
    assert proposals[0].resolution is None


def test_reconcile_resolution_choice():
    rec = ProseReconciler()
    p = ProseReconciler().detect(set(), ["new fact"], "P1")[0]
    assert rec.resolve(p, "language").resolution == "language"
    assert rec.resolve(p, "model").resolution == "model"
    with pytest.raises(ValueError):
        rec.resolve(p, "neither")
