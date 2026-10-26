"""Semantic conflict detection for merges.

Textual merge rules are insufficient: two branches may edit different records
yet conflict at the narrative level (SRS REQ-098). This module compares the
accepted deltas of two branches and reports conflicts the merge validator must
surface before a merge commit.

An operation delta is a plain dict with a ``kind`` and operation-specific keys.
Recognized kinds:

- ``"assert"`` -- ``{object_id, key, value, story_time, scope, model_id}``
- ``"knowledge"`` -- ``{actor_id, proposition, known: bool, story_time}``
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticConflict:
    """A narrative-level incompatibility between two branch deltas.

    :ivar kind: the conflict category (``assertion`` or ``knowledge``).
    :ivar subject: the object/actor the conflict concerns.
    :ivar detail: a human-readable explanation naming both sides.
    """

    kind: str
    subject: str
    detail: str


def detect_semantic_conflicts(
    delta_a: list[dict], delta_b: list[dict]
) -> list[SemanticConflict]:
    """Return the semantic conflicts between two sets of accepted operations.

    :param delta_a: operations accepted on the first branch.
    :param delta_b: operations accepted on the second branch.
    :returns: a list of :class:`SemanticConflict`; empty when the deltas are
        narratively compatible.

    Detects (1) incompatible assertions -- the same object/key/story time set to
    different values with the same scope and model; and (2) knowledge conflicts
    -- one branch says an actor lacks a proposition while the other makes them
    act on it.
    """

    conflicts: list[SemanticConflict] = []

    asserts_a = [o for o in delta_a if o.get("kind") == "assert"]
    asserts_b = [o for o in delta_b if o.get("kind") == "assert"]
    for a in asserts_a:
        for b in asserts_b:
            if (
                a.get("object_id") == b.get("object_id")
                and a.get("key") == b.get("key")
                and a.get("story_time") == b.get("story_time")
                and a.get("scope") == b.get("scope")
                and a.get("model_id") == b.get("model_id")
                and a.get("value") != b.get("value")
            ):
                conflicts.append(
                    SemanticConflict(
                        kind="assertion",
                        subject=str(a.get("object_id")),
                        detail=(
                            f"{a['object_id']}.{a['key']} at t={a.get('story_time')} is "
                            f"{a.get('value')!r} on one branch and {b.get('value')!r} on the other"
                        ),
                    )
                )

    know_a = {(o["actor_id"], o["proposition"]): o for o in delta_a if o.get("kind") == "knowledge"}
    know_b = {(o["actor_id"], o["proposition"]): o for o in delta_b if o.get("kind") == "knowledge"}
    for key, oa in know_a.items():
        ob = know_b.get(key)
        if ob is not None and bool(oa.get("known")) != bool(ob.get("known")):
            conflicts.append(
                SemanticConflict(
                    kind="knowledge",
                    subject=str(key[0]),
                    detail=(
                        f"{key[0]} knows {key[1]!r}={oa.get('known')} on one branch but "
                        f"{ob.get('known')} on the other"
                    ),
                )
            )

    return conflicts
