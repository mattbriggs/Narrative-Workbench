"""Tests for the append-only repository and branch lifecycle (SRS SS3.9)."""

import pytest

from nw_engine.contracts.models import ActorRole, AuthorityState, BranchState, Origin
from nw_engine.errors import EngineError, ParentChangedError
from nw_engine.provenance import build_provenance
from nw_engine.repository import Repository, detect_semantic_conflicts


def prov(decision="ok"):
    return build_provenance(
        origin=Origin.HUMAN,
        actor=ActorRole.NARRATIVE_DESIGNER,
        authority=AuthorityState.ALLOWED,
        decision=decision,
    )


@pytest.fixture()
def repo():
    r = Repository()
    r.create_root_commit("main", ActorRole.NARRATIVE_DESIGNER, prov("root"))
    return r


def test_append_only_commits(repo):
    head = repo.head("main")
    repo.record_op("op1", "assert", {"object_id": "a", "key": "trust", "value": "high", "story_time": 1})
    c1 = repo.commit("main", head, ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov(), ["op1"])
    assert repo.head("main") == c1.id
    assert repo.lineage(c1.id) == [head, c1.id]


def test_commit_rejects_stale_parent(repo):
    head = repo.head("main")
    repo.commit("main", head, ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov())
    with pytest.raises(ParentChangedError):
        repo.commit("main", head, ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov())


def test_duplicate_op_rejected(repo):
    repo.record_op("op1", "assert", {"value": 1})
    with pytest.raises(EngineError):
        repo.record_op("op1", "assert", {"value": 2})


def test_rewind_preserves_history(repo):
    head = repo.head("main")
    c1 = repo.commit("main", head, ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov())
    old = repo.rewind("main", head)
    assert old == c1.id
    assert repo.head("main") == head
    # c1 is still retrievable (not deleted).
    assert c1.id in repo.lineage(c1.id)


def test_rewind_unknown_commit(repo):
    with pytest.raises(EngineError):
        repo.rewind("main", "nope")


def test_branch_lifecycle_transitions(repo):
    repo.create_branch("feature", repo.head("main"))
    assert repo.branch_state("feature") is BranchState.ACTIVE
    repo.set_branch_state("feature", BranchState.IN_REVIEW)
    repo.set_branch_state("feature", BranchState.MERGE_READY)
    repo.set_branch_state("feature", BranchState.ACTIVE)
    repo.set_branch_state("feature", BranchState.ARCHIVED)
    repo.set_branch_state("feature", BranchState.ACTIVE)  # restore


def test_illegal_branch_transition(repo):
    repo.create_branch("feature", repo.head("main"))
    with pytest.raises(EngineError):
        repo.set_branch_state("feature", BranchState.MERGE_READY)  # not from ACTIVE


def test_duplicate_branch_and_unknown_source(repo):
    with pytest.raises(EngineError):
        repo.create_branch("main", repo.head("main"))
    with pytest.raises(EngineError):
        repo.create_branch("feature", "nope")


def test_root_commit_duplicate_branch(repo):
    with pytest.raises(EngineError):
        repo.create_root_commit("main", ActorRole.NARRATIVE_DESIGNER, prov())


def test_commit_unknown_branch(repo):
    with pytest.raises(EngineError):
        repo.commit("nobranch", None, ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov())


def test_merge_without_conflict(repo):
    repo.record_op("o1", "assert", {"object_id": "a", "key": "trust", "value": "high", "story_time": 1})
    repo.commit("main", repo.head("main"), ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov(), ["o1"])
    repo.create_branch("feature", repo.head("main"))
    repo.record_op("o2", "assert", {"object_id": "b", "key": "fear", "value": "low", "story_time": 2})
    repo.commit("feature", repo.head("feature"), ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov(), ["o2"])
    merged = repo.merge("main", "feature", ActorRole.NARRATIVE_DESIGNER, prov("merge"))
    assert merged.provenance.inputs["merged_from"] == repo.head("feature")


def test_merge_with_conflict_is_blocked(repo):
    repo.record_op("o1", "assert", {"object_id": "a", "key": "trust", "value": "high", "story_time": 1, "scope": None, "model_id": None})
    repo.commit("main", repo.head("main"), ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov(), ["o1"])
    repo.create_branch("feature", repo.head("main"))
    # Feature sets the same assertion to a different value -> semantic conflict.
    repo.record_op("o2", "assert", {"object_id": "a", "key": "trust", "value": "low", "story_time": 1, "scope": None, "model_id": None})
    repo.commit("feature", repo.head("feature"), ActorRole.NARRATIVE_DESIGNER, AuthorityState.ALLOWED, prov(), ["o2"])
    assert repo.semantic_conflicts("main", "feature")
    with pytest.raises(EngineError):
        repo.merge("main", "feature", ActorRole.NARRATIVE_DESIGNER, prov("merge"))


def test_detect_semantic_conflicts_knowledge():
    a = [{"kind": "knowledge", "actor_id": "A", "proposition": "secret", "known": False}]
    b = [{"kind": "knowledge", "actor_id": "A", "proposition": "secret", "known": True}]
    conflicts = detect_semantic_conflicts(a, b)
    assert len(conflicts) == 1 and conflicts[0].kind == "knowledge"
