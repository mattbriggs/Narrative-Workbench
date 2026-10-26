"""Append-only versioned repository with branch lifecycle.

Implements the commit model (SRS REQ-090), the branch lifecycle state machine
(SRS REQ-093), non-destructive rewind (SRS REQ-096), and semantic-conflict-aware
merge (SRS REQ-098). This is an in-memory reference adapter behind a stable
port; a SQLite/object-store adapter replaces it without changing callers
(SRS REQ-171, implementation plan A-3).

:side effects: mutates in-memory dictionaries only. Commits are never mutated
    after creation; branch pointers move but no commit is deleted.
"""

from __future__ import annotations

import logging
from typing import Optional

from nw_engine.contracts.models import (
    ActorRole,
    AuthorityState,
    BranchState,
    Commit,
    ProvenanceRecord,
)
from nw_engine.errors import EngineError, ParentChangedError
from nw_engine.repository.conflicts import SemanticConflict, detect_semantic_conflicts

logger = logging.getLogger(__name__)

# Permitted branch-lifecycle transitions (SRS REQ-093). Maps a state to the set
# of states reachable from it. Enforced by :meth:`Repository.set_branch_state`.
_BRANCH_TRANSITIONS: dict[BranchState, set[BranchState]] = {
    BranchState.ACTIVE: {BranchState.IN_REVIEW, BranchState.ARCHIVED},
    BranchState.IN_REVIEW: {BranchState.ACTIVE, BranchState.MERGE_READY, BranchState.PUBLISHED},
    BranchState.MERGE_READY: {BranchState.ACTIVE},
    BranchState.PUBLISHED: set(),
    BranchState.ARCHIVED: {BranchState.ACTIVE},
}


class Repository:
    """In-memory append-only repository.

    :ivar _ops: append-only operation records keyed by op id.
    :ivar _commits: immutable commits keyed by commit id.
    :ivar _heads: branch id -> head commit id.
    :ivar _branch_state: branch id -> :class:`BranchState`.
    """

    def __init__(self) -> None:
        self._ops: dict[str, dict] = {}
        self._commits: dict[str, Commit] = {}
        self._heads: dict[str, Optional[str]] = {}
        self._branch_state: dict[str, BranchState] = {}
        self._seq = 0

    # -- operations --------------------------------------------------------

    def record_op(self, op_id: str, kind: str, delta: dict) -> None:
        """Append an operation to the immutable log.

        :param op_id: unique operation id.
        :param kind: operation kind (e.g. ``"assert"``, ``"knowledge"``).
        :param delta: the accepted delta payload.
        :raises EngineError: if the op id already exists (append-only).
        """

        if op_id in self._ops:
            raise EngineError(f"operation {op_id} already recorded", scope=op_id)
        self._ops[op_id] = {"id": op_id, "kind": kind, **delta}

    def op(self, op_id: str) -> dict:
        """Return a recorded operation by id."""

        return self._ops[op_id]

    # -- commits and branches ---------------------------------------------

    def create_root_commit(
        self,
        branch_id: str,
        actor: ActorRole,
        provenance: ProvenanceRecord,
        op_ids: Optional[list[str]] = None,
        message: str = "root",
    ) -> Commit:
        """Create the root commit of a branch (e.g. a frozen source import).

        :returns: the new root :class:`Commit`.
        :raises EngineError: if the branch already exists.
        """

        if branch_id in self._heads:
            raise EngineError(f"branch {branch_id} already exists", scope=branch_id)
        commit = self._new_commit(branch_id, None, actor, provenance, op_ids or [], [], message)
        self._heads[branch_id] = commit.id
        self._branch_state[branch_id] = BranchState.ACTIVE
        return commit

    def commit(
        self,
        branch_id: str,
        expected_parent: Optional[str],
        actor: ActorRole,
        authority: AuthorityState,
        provenance: ProvenanceRecord,
        op_ids: Optional[list[str]] = None,
        alternatives: Optional[list[str]] = None,
        message: str = "",
    ) -> Commit:
        """Commit a validated delta onto a branch.

        :param expected_parent: the commit the caller accepted against; if the
            branch head has moved, the commit is refused (SRS REQ-078).
        :raises ParentChangedError: if the branch head != ``expected_parent``.
        :raises EngineError: if the branch is unknown.
        """

        if branch_id not in self._heads:
            raise EngineError(f"unknown branch {branch_id}", scope=branch_id)
        head = self._heads[branch_id]
        if head != expected_parent:
            raise ParentChangedError(
                f"branch {branch_id} head moved from {expected_parent} to {head}",
                scope=branch_id,
            )
        commit = self._new_commit(
            branch_id, head, actor, provenance, op_ids or [], alternatives or [], message
        )
        self._heads[branch_id] = commit.id
        return commit

    def head(self, branch_id: str) -> Optional[str]:
        """Return the current head commit id of a branch."""

        return self._heads[branch_id]

    def branch_state(self, branch_id: str) -> BranchState:
        """Return the lifecycle state of a branch."""

        return self._branch_state[branch_id]

    def create_branch(self, new_branch_id: str, from_commit: str) -> None:
        """Create a new branch pointing at an existing commit.

        :raises EngineError: on duplicate branch id or unknown source commit.
        """

        if new_branch_id in self._heads:
            raise EngineError(f"branch {new_branch_id} already exists", scope=new_branch_id)
        if from_commit not in self._commits:
            raise EngineError(f"unknown commit {from_commit}", scope=from_commit)
        self._heads[new_branch_id] = from_commit
        self._branch_state[new_branch_id] = BranchState.ACTIVE

    def rewind(self, branch_id: str, to_commit: str) -> str:
        """Move a branch pointer to an earlier commit without deleting history.

        :returns: the previous head commit id (still retained).
        :raises EngineError: if the target commit is unknown.
        """

        if to_commit not in self._commits:
            raise EngineError(f"unknown commit {to_commit}", scope=to_commit)
        old = self._heads[branch_id]
        self._heads[branch_id] = to_commit
        # The old head and its lineage remain in _commits (never deleted).
        return old or ""

    def lineage(self, commit_id: str) -> list[str]:
        """Return the commit ids from root to ``commit_id`` inclusive."""

        chain: list[str] = []
        cur: Optional[str] = commit_id
        while cur is not None:
            chain.append(cur)
            cur = self._commits[cur].parent_id
        return list(reversed(chain))

    def accumulated_delta(self, commit_id: str) -> list[dict]:
        """Return all operations along a commit's lineage, in order."""

        ops: list[dict] = []
        for cid in self.lineage(commit_id):
            for op_id in self._commits[cid].op_ids:
                ops.append(self._ops[op_id])
        return ops

    def set_branch_state(self, branch_id: str, target: BranchState) -> None:
        """Advance a branch through its lifecycle, enforcing permitted edges.

        :raises EngineError: if the transition is not permitted (SRS REQ-093).
        """

        current = self._branch_state[branch_id]
        if target not in _BRANCH_TRANSITIONS[current]:
            raise EngineError(
                f"illegal branch transition {current.value} -> {target.value}",
                scope=branch_id,
            )
        self._branch_state[branch_id] = target

    def merge(
        self,
        target_branch: str,
        source_branch: str,
        actor: ActorRole,
        provenance: ProvenanceRecord,
        message: str = "merge",
    ) -> Commit:
        """Merge a source branch into a target, creating a new commit.

        The parents are never rewritten; the merged source is recorded in
        provenance inputs (SRS REQ-090). The merge is refused if semantic
        conflicts remain (SRS REQ-098).

        :raises EngineError: with code ``HARD_INVARIANT`` listing the conflicts
            when the branches are narratively incompatible.
        """

        conflicts = self.semantic_conflicts(target_branch, source_branch)
        if conflicts:
            raise EngineError(
                "unresolved semantic conflicts: "
                + "; ".join(c.detail for c in conflicts),
                scope=target_branch,
            )
        target_head = self._heads[target_branch]
        source_head = self._heads[source_branch]
        merged_prov = provenance.model_copy(
            update={"inputs": {**provenance.inputs, "merged_from": source_head}}
        )
        commit = self._new_commit(
            target_branch, target_head, actor, merged_prov, [], [], message
        )
        self._heads[target_branch] = commit.id
        return commit

    def semantic_conflicts(
        self, branch_a: str, branch_b: str
    ) -> list[SemanticConflict]:
        """Return the semantic conflicts between two branches' accumulated deltas."""

        return detect_semantic_conflicts(
            self.accumulated_delta(self._heads[branch_a]),
            self.accumulated_delta(self._heads[branch_b]),
        )

    # -- internals ---------------------------------------------------------

    def _new_commit(
        self,
        branch_id: str,
        parent_id: Optional[str],
        actor: ActorRole,
        provenance: ProvenanceRecord,
        op_ids: list[str],
        alternatives: list[str],
        message: str,
    ) -> Commit:
        self._seq += 1
        commit = Commit(
            id=f"c{self._seq:04d}",
            parent_id=parent_id,
            branch_id=branch_id,
            actor=actor,
            authority=provenance.authority,
            op_ids=list(op_ids),
            provenance=provenance,
            accepted_alternatives=list(alternatives),
            message=message,
        )
        self._commits[commit.id] = commit
        return commit
