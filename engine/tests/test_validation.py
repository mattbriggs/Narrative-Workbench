"""Tests for the hard-invariant validation engine (SRS SS8.3)."""

import pytest

from nw_engine.contracts.models import Mode
from nw_engine.validation import ValidationEngine


@pytest.fixture()
def engine():
    return ValidationEngine()


def test_empty_payload_passes(engine):
    r = engine.validate({})
    assert r.passed and not r.hard_failures and r.validator_version


def test_knowledge_invariant(engine):
    bad = engine.validate({
        "knowledge_requirements": [{"actor_id": "A", "proposition": "secret"}],
        "knowledge": {"A": []},
    })
    assert not bad.passed
    assert bad.hard_failures[0].rule == "knowledge"
    good = engine.validate({
        "knowledge_requirements": [{"actor_id": "A", "proposition": "secret"}],
        "knowledge": {"A": ["secret"]},
    })
    assert good.passed
    inferred = engine.validate({
        "knowledge_requirements": [{"actor_id": "A", "proposition": "secret", "inference_path": "deduced"}],
        "knowledge": {"A": []},
    })
    assert inferred.passed


def test_location_time_invariant(engine):
    r = engine.validate({
        "placements": [
            {"object_id": "o", "place": "hall", "story_time": 1},
            {"object_id": "o", "place": "garden", "story_time": 1},
        ]
    })
    assert not r.passed and r.hard_failures[0].rule == "location_time"
    ok = engine.validate({
        "placements": [
            {"object_id": "o", "place": "hall", "story_time": 1},
            {"object_id": "o", "place": "garden", "story_time": 2},
        ]
    })
    assert ok.passed


def test_disclosure_invariant(engine):
    r = engine.validate({"disclosures": [{"fact": "letter", "becomes_public": True}]})
    assert not r.passed and r.hard_failures[0].rule == "disclosure"
    ok = engine.validate({"disclosures": [{"fact": "letter", "becomes_public": True, "mechanism": "overheard"}]})
    assert ok.passed


def test_discourse_invariant(engine):
    r = engine.validate({"discourse": {"pov": "first", "contract_pov": "third", "narrative_time": "past", "contract_time": "past"}})
    assert not r.passed and r.hard_failures[0].rule == "discourse"
    ok = engine.validate({"discourse": {"pov": "first", "contract_pov": "third", "narrative_time": "past", "contract_time": "past", "operator_applied": True}})
    assert ok.passed


def test_source_integrity_invariant(engine):
    r = engine.validate({"required_anchor_resolution": [{"anchor_id": "a1", "resolves": False}]})
    assert not r.passed and r.hard_failures[0].rule == "source_integrity"


def test_mode_authority_invariant(engine):
    r = engine.validate({"mode_authority": {"action": "overwrite", "target": "frozen_source", "mode": Mode.COUNTERFACTUAL.value}})
    assert not r.passed and r.hard_failures[0].rule == "mode_authority"
    ok = engine.validate({"mode_authority": {"action": "overwrite", "target": "experiment", "mode": Mode.COUNTERFACTUAL.value}})
    assert ok.passed


def test_motivation_is_soft_warning_not_hard(engine):
    r = engine.validate({"removed_motivations": [{"actor_id": "A", "motivation": "revenge"}]})
    assert r.passed  # soft, not hard
    assert any(g.name == "motivation_continuity" for g in r.soft_goals)
    withcause = engine.validate({"removed_motivations": [{"actor_id": "A", "motivation": "revenge", "cause": "forgiven"}]})
    assert not withcause.soft_goals


def test_soft_goals_passed_through_and_uncertainty(engine):
    r = engine.validate({
        "soft_goals": [{"name": "tension", "score": 0.8, "rationale": "rising"}],
        "uncertainty": "moderate",
    })
    assert r.soft_goals[0].name == "tension"
    assert r.uncertainty == "moderate"


def test_multiple_hard_failures_aggregate(engine):
    r = engine.validate({
        "disclosures": [{"fact": "x", "becomes_public": True}],
        "required_anchor_resolution": [{"anchor_id": "a", "resolves": False}],
    })
    assert len(r.hard_failures) == 2
