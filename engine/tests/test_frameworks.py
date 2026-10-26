"""Tests for structural frameworks and episode contracts (SRS SS3.4, REQ-030..033)."""

import pytest

from nw_engine.contracts.models import StateObject
from nw_engine.frameworks import (
    ClosureBehavior,
    EpisodeContract,
    FrameworkRegistry,
    StructuralFramework,
)
from nw_engine.graph import GraphKernel


@pytest.fixture()
def kernel():
    k = GraphKernel()
    k.add_unit("work", "work")
    k.add_unit("act1", "act", parent="work")
    k.add_unit("sc1", "scene", parent="act1")
    k.add_body(StateObject(id="actorA", kind="actor"), unit_id="sc1")  # non-unit node is skipped
    return k


def test_same_graph_under_several_frameworks(kernel):
    reg = FrameworkRegistry()
    reg.register(StructuralFramework(
        name="three-act", version="1",
        permitted_unit_types={"work", "act", "scene"},
        containment={"act": {"work"}, "scene": {"act"}},
        milestones={"act1"},
    ))
    reg.register(StructuralFramework(
        name="open", version="1",
        permitted_unit_types={"work", "scene"},  # no 'act' -> violation
    ))
    results = reg.evaluate_all(kernel)
    assert results[("three-act", "1")] == []  # conforms
    open_violations = results[("open", "1")]
    assert any(v.unit_id == "act1" and v.rule == "unit_type" for v in open_violations)


def test_containment_violation(kernel):
    fw = StructuralFramework(
        name="strict", version="1",
        permitted_unit_types={"work", "act", "scene"},
        containment={"scene": {"work"}},  # scene must be under work, but it's under act
    )
    violations = fw.evaluate(kernel)
    assert any(v.unit_id == "sc1" and v.rule == "containment" for v in violations)


def test_milestone_and_duplicate_registration(kernel):
    fw = StructuralFramework(name="f", version="1", permitted_unit_types={"work", "act", "scene"}, milestones={"act1"})
    assert fw.is_milestone("act1") and not fw.is_milestone("sc1")
    reg = FrameworkRegistry()
    reg.register(fw)
    with pytest.raises(ValueError):
        reg.register(fw)
    assert reg.get("f", "1") is fw


def test_episode_mutation_rules():
    ec = EpisodeContract(
        episode_id="ep1",
        allowed_mutations={"tension"},
        preserved_invariants={"protagonist_identity"},
    )
    ec.validate_mutation("tension")  # allowed
    with pytest.raises(ValueError):
        ec.validate_mutation("protagonist_identity")  # preserved
    with pytest.raises(ValueError):
        ec.validate_mutation("setting")  # not in allowed set


def test_episode_propagation_by_closure():
    ledger: dict = {}
    accumulate = EpisodeContract(episode_id="ep1", exit_effects={"reputation": "raised"}, closure=ClosureBehavior.ACCUMULATE)
    accumulate.propagate(ledger)
    assert ledger == {"reputation": "raised"}

    restore = EpisodeContract(episode_id="ep2", exit_effects={"reputation": "lost"}, closure=ClosureBehavior.RESTORE)
    restore.propagate(ledger)
    assert ledger == {"reputation": "raised"}  # restore persists nothing


def test_episode_propagation_skips_preserved_invariants():
    ledger: dict = {}
    ec = EpisodeContract(
        episode_id="ep3",
        exit_effects={"world_rules": "changed", "mood": "dark"},
        preserved_invariants={"world_rules"},
        closure=ClosureBehavior.EXPAND,
    )
    ec.propagate(ledger)
    assert ledger == {"mood": "dark"}
