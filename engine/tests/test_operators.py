"""Tests for formal operators and reader-model transitions (SRS SS3.4, REQ-034/035)."""

import pytest

from nw_engine.contracts.models import Event, StateObject
from nw_engine.domain.vocabulary import RelationshipType
from nw_engine.errors import GraphConstraintError
from nw_engine.graph import GraphKernel
from nw_engine.operators import (
    DEFAULT_OPERATORS,
    FormalOperator,
    OperatorLibrary,
    OperatorName,
    reader_model_transition,
)


def test_all_eight_operators_present():
    assert set(DEFAULT_OPERATORS) == set(OperatorName)
    # None of the default operators assert diegetic cause.
    assert all(op.relation is not RelationshipType.CAUSES for op in DEFAULT_OPERATORS.values())


def test_collage_juxtaposes_without_causal_edge():
    k = GraphKernel()
    k.add_unit("frag1", "work")
    k.add_unit("frag2", "work")
    lib = OperatorLibrary()
    collage = lib.get(OperatorName.COLLAGE)
    collage.apply(k, "frag2", "frag1")
    assert ("frag2", "frag1") in k.edges_of(RelationshipType.PART_OF)
    assert k.edges_of(RelationshipType.CAUSES) == []


def test_operator_refuses_to_assert_cause():
    k = GraphKernel()
    k.add_unit("a", "scene")
    k.add_unit("b", "scene")
    bad = FormalOperator(OperatorName.INTERRUPT, "scene", RelationshipType.CAUSES, True, False)
    with pytest.raises(GraphConstraintError):
        bad.apply(k, "a", "b", claim="x", scope="s")


def test_reinterpret_targets_events():
    k = GraphKernel()
    k.add_unit("w", "work")
    k.add_body(StateObject(id="reader", kind="reader_expectation"))
    k.add_event(Event(id="e1", description="guidance", story_time=1))
    op = OperatorLibrary().get(OperatorName.REINTERPRET)
    op.apply(k, "reader", "e1")
    assert ("reader", "e1") in k.edges_of(RelationshipType.REINTERPRETS)


def test_inconsistency_classification():
    collage = DEFAULT_OPERATORS[OperatorName.COLLAGE]  # preserves ambiguity
    interrupt = DEFAULT_OPERATORS[OperatorName.INTERRUPT]  # does not
    assert collage.classify_inconsistency(True) == "intentional"
    assert interrupt.classify_inconsistency(True) == "accidental"
    assert collage.classify_inconsistency(False) == "none"


def test_register_custom_operator():
    lib = OperatorLibrary()
    custom = FormalOperator(OperatorName.SPIRAL, "work", RelationshipType.PART_OF, False, True)
    lib.register(custom)
    assert lib.get(OperatorName.SPIRAL).target_scale == "work"


def test_reader_model_transition_has_no_cause():
    mt = reader_model_transition("interruptions recognized", ["e1", "e2"], ["revise genre expectation"], is_epiphany=True)
    assert mt.affected_model == "reader"
    assert mt.reinterpreted_events == ["e1", "e2"]
    assert mt.is_epiphany is True
