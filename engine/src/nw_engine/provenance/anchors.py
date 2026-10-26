"""Evidence anchors (**pins**) and the publication gate.

An anchor is a stable reference into a frozen source edition. A broken anchor
blocks publication until it is realigned (SRS REQ-057). Source content is never
mutated here (SRS REQ-051).
"""

from __future__ import annotations

from nw_engine.contracts.models import EvidenceAnchor
from nw_engine.errors import AnchorBrokenError, SourceImmutableError


class AnchorStore:
    """Holds evidence anchors against fingerprinted source editions.

    :ivar _editions: maps a source edition id to its immutable fingerprint.
    :ivar _anchors: maps an anchor id to its :class:`EvidenceAnchor`.
    """

    def __init__(self) -> None:
        self._editions: dict[str, str] = {}
        self._anchors: dict[str, EvidenceAnchor] = {}

    def freeze_edition(self, edition_id: str, fingerprint: str) -> None:
        """Register a frozen source edition.

        :param edition_id: the edition's stable id.
        :param fingerprint: the content fingerprint that pins the edition.
        :raises SourceImmutableError: if the edition already exists with a
            different fingerprint (re-import is a new root, not an overwrite).
        """

        if edition_id in self._editions and self._editions[edition_id] != fingerprint:
            raise SourceImmutableError(
                f"source edition {edition_id} is frozen and cannot be re-fingerprinted",
                scope=edition_id,
            )
        self._editions[edition_id] = fingerprint

    def add_anchor(self, anchor: EvidenceAnchor) -> None:
        """Add an evidence anchor into a frozen edition.

        :param anchor: the :class:`EvidenceAnchor`.
        :raises AnchorBrokenError: if the edition is unknown or the fingerprint
            does not match the frozen edition (SRS REQ-057 source integrity).
        """

        fp = self._editions.get(anchor.source_edition_id)
        if fp is None:
            raise AnchorBrokenError(
                f"no frozen edition {anchor.source_edition_id}", scope=anchor.id
            )
        if fp != anchor.fingerprint:
            raise AnchorBrokenError(
                f"anchor {anchor.id} does not match frozen edition fingerprint",
                scope=anchor.id,
            )
        self._anchors[anchor.id] = anchor

    def resolves(self, anchor_id: str) -> bool:
        """Return whether an anchor currently resolves to its frozen edition."""

        anchor = self._anchors.get(anchor_id)
        if anchor is None:
            return False
        return anchor.resolves and self._editions.get(anchor.source_edition_id) == anchor.fingerprint

    def break_anchor(self, anchor_id: str) -> None:
        """Mark an anchor broken (e.g. after a re-import changed the edition)."""

        if anchor_id in self._anchors:
            self._anchors[anchor_id] = self._anchors[anchor_id].model_copy(update={"resolves": False})

    def publication_status(self, required_anchor_ids: list[str]) -> str:
        """Return ``"ready"`` or ``"blocked"`` for a set of required anchors.

        :param required_anchor_ids: anchors a claim depends on.
        :returns: ``"blocked"`` if any required anchor is unresolved, else
            ``"ready"`` (SRS REQ-057).
        """

        for aid in required_anchor_ids:
            if not self.resolves(aid):
                return "blocked"
        return "ready"
