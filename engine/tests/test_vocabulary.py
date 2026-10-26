"""Tests for the fixed narrative vocabulary (SRS SS1.3.1, REQ-013)."""

import pytest

from nw_engine.domain import (
    AssertionLevel,
    RelationshipType,
    StateFieldTerm,
    TransitionClass,
    STATE_FIELD_GLOSSARY,
    relationship_constraint,
)


def test_state_field_terms_are_exactly_the_seven_fixed_names():
    assert {t.value for t in StateFieldTerm} == {
        "body", "impulse", "boundary", "sink", "gate", "pin", "ghost",
    }


def test_glossary_covers_every_term_and_ghost_is_undefined():
    assert set(STATE_FIELD_GLOSSARY) == set(StateFieldTerm)
    assert "Not yet defined" in STATE_FIELD_GLOSSARY[StateFieldTerm.GHOST]


@pytest.mark.parametrize("rel", list(RelationshipType))
def test_every_relationship_has_a_constraint(rel):
    assert relationship_constraint(rel)


def test_transition_classes_and_assertion_levels_present():
    assert TransitionClass.ONTOLOGICAL.value == "ontological"
    assert [l.value for l in AssertionLevel] == ["observation", "finding", "claim"]
