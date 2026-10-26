"""Tests for the counterfactual comparison matrix (SRS REQ-063..066)."""

import pytest

from nw_engine.contracts.models import Diff
from nw_engine.projections import ComparisonBuilder, DIMENSIONS


def test_matrix_has_seven_dimensions_and_provenance():
    b = ComparisonBuilder("c-base", "x-move-disclosure", ["world_rules"])
    comp = b.build()
    assert [r.dimension for r in comp.rows] == list(DIMENSIONS)
    assert comp.provenance.inputs["baseline"] == "c-base"


def test_deterministic_and_hypotheses_are_separate():
    b = ComparisonBuilder("c-base", "x1")
    b.add_deterministic("World", Diff(label="Changed", subject="letter location", before="final", after="midpoint"))
    b.add_hypothesis("Affective", Diff(label="Changed", subject="tension", before="low", after="high"))
    comp = b.build()
    world = next(r for r in comp.rows if r.dimension == "World")
    affective = next(r for r in comp.rows if r.dimension == "Affective")
    assert world.deterministic and not world.hypotheses
    assert affective.hypotheses and not affective.deterministic


def test_unknown_dimension_and_bad_label_rejected():
    b = ComparisonBuilder("c", "x")
    with pytest.raises(ValueError):
        b.add_deterministic("Nope", Diff(label="Added", subject="s"))
    with pytest.raises(ValueError):
        b.add_deterministic("World", Diff(label="Mutated", subject="s"))


def test_reader_model_rejects_measured_response():
    b = ComparisonBuilder("c", "x")
    with pytest.raises(ValueError):
        b.add_hypothesis("Reader model", Diff(label="Changed", subject="measured reader surprise"))
    # Intended response is fine.
    b.add_hypothesis("Reader model", Diff(label="Changed", subject="intended surprise"))


def test_unresolved_constraints_recorded():
    b = ComparisonBuilder("c", "x")
    b.add_unresolved("two soft constraints conflict")
    assert b.build().unresolved_constraints == ["two soft constraints conflict"]
