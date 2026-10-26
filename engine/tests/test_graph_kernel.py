"""Tests for the typed graph kernel (SRS REQ-010 to REQ-016)."""

import pytest

from nw_engine.contracts.models import Event, StateAssertion, StateObject
from nw_engine.domain.vocabulary import RelationshipType
from nw_engine.errors import GraphConstraintError
from nw_engine.graph import GraphKernel


@pytest.fixture()
def kernel():
    k = GraphKernel()
    k.add_unit("work", "work")
    k.add_unit("scene1", "scene", parent="work")
    k.add_body(StateObject(id="actorA", kind="actor", label="A", mass=3.0), unit_id="scene1")
    k.add_body(StateObject(id="actorB", kind="actor", label="B", mass=1.0))
    k.add_event(Event(id="e1", unit_id="scene1", description="letter arrives", story_time=1))
    return k


def test_mass_and_bodies(kernel):
    assert kernel.mass("actorA") == 3.0
    assert set(kernel.bodies()) == {"actorA", "actorB"}


def test_mass_rejects_non_body(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.mass("scene1")


def test_duplicate_id_rejected(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.add_unit("scene1", "scene")


def test_unknown_parent_rejected():
    k = GraphKernel()
    with pytest.raises(GraphConstraintError):
        k.add_unit("x", "scene", parent="missing")


def test_containment_is_projection(kernel):
    assert kernel.contained_by("work") == ["scene1"]


def test_causes_requires_claim_and_scope(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.add_edge("e1", "actorB", RelationshipType.CAUSES)
    kernel.add_edge("e1", "actorB", RelationshipType.CAUSES, claim="letter alarms B", scope="scene1")
    assert ("e1", "actorB") in kernel.edges_of(RelationshipType.CAUSES)


def test_reinterprets_must_target_event(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.add_edge("actorA", "actorB", RelationshipType.REINTERPRETS)
    kernel.add_edge("actorA", "e1", RelationshipType.REINTERPRETS)
    assert ("actorA", "e1") in kernel.edges_of(RelationshipType.REINTERPRETS)


def test_derived_from_requires_source_version(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.add_edge("actorA", "actorB", RelationshipType.DERIVED_FROM)


def test_events_sorted_by_story_time(kernel):
    kernel.add_event(Event(id="e0", unit_id="scene1", description="earlier", story_time=0))
    assert kernel.events() == ["e0", "e1"]


def test_assertion_conflict_requires_scope_or_contradiction(kernel):
    kernel.add_assertion(StateAssertion(id="s1", object_id="actorA", key="trust", value="high", story_time=1))
    with pytest.raises(GraphConstraintError):
        kernel.add_assertion(
            StateAssertion(id="s2", object_id="actorA", key="trust", value="low", story_time=1)
        )
    # Different scope is allowed.
    kernel.add_assertion(
        StateAssertion(id="s3", object_id="actorA", key="trust", value="low", story_time=1, scope="belief")
    )
    assert len(kernel.assertions_for("actorA")) == 2


def test_assertion_on_unknown_body_rejected(kernel):
    with pytest.raises(GraphConstraintError):
        kernel.add_assertion(StateAssertion(id="s9", object_id="ghostbody", key="x", value=1))


def test_node_count(kernel):
    assert kernel.node_count("body") == 2
    assert kernel.node_count() == 5  # work, scene1, actorA, actorB, e1
