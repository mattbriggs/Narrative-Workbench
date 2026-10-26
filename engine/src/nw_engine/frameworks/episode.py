"""Episode continuity contracts (SRS REQ-033).

An episode declares what it inherits, what it may change, what must survive, and
how it closes. Exit effects propagate selected changes into a shared ledger so
episodes close independently while cumulative changes persist (NW ADD v1.1
Table 11; SRS validation scenario "episodic quest cycle").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ClosureBehavior(str, Enum):
    """How an episode closes."""

    RESOLVE = "resolve"
    RESTORE = "restore"
    ACCUMULATE = "accumulate"
    EXPAND = "expand"
    RECONTEXTUALIZE = "recontextualize"


@dataclass
class EpisodeContract:
    """A declaration governing one episode.

    :ivar episode_id: the episode this contract governs.
    :ivar inherited_state: world/character/thematic assertions entering the episode.
    :ivar allowed_mutations: inherited keys this episode may change.
    :ivar preserved_invariants: keys that must survive regardless of trajectory.
    :ivar exit_effects: changes that persist into the shared ledger.
    :ivar closure: the :class:`ClosureBehavior`.
    """

    episode_id: str
    inherited_state: dict[str, object] = field(default_factory=dict)
    allowed_mutations: set[str] = field(default_factory=set)
    preserved_invariants: set[str] = field(default_factory=set)
    exit_effects: dict[str, object] = field(default_factory=dict)
    closure: ClosureBehavior = ClosureBehavior.RESOLVE

    def validate_mutation(self, key: str) -> None:
        """Raise if a mutation targets a preserved invariant or a key not allowed.

        :raises ValueError: if ``key`` is a preserved invariant, or not in
            ``allowed_mutations`` when that set is non-empty.
        """

        if key in self.preserved_invariants:
            raise ValueError(f"{key!r} is a preserved invariant of episode {self.episode_id}")
        if self.allowed_mutations and key not in self.allowed_mutations:
            raise ValueError(f"{key!r} is not an allowed mutation of episode {self.episode_id}")

    def propagate(self, shared_ledger: dict[str, object]) -> dict[str, object]:
        """Apply exit effects to the shared ledger per closure behavior.

        - ``RESTORE`` persists nothing (the episode returns near its start).
        - every other closure writes ``exit_effects`` into the ledger.

        :param shared_ledger: the cross-episode ledger (mutated in place).
        :returns: the updated ledger.
        """

        if self.closure is ClosureBehavior.RESTORE:
            return shared_ledger
        for key, value in self.exit_effects.items():
            if key in self.preserved_invariants:
                continue
            shared_ledger[key] = value
        return shared_ledger
