"""Source ingestion and segmentation.

The ingestor computes a content fingerprint, freezes the edition in an
:class:`~nw_engine.provenance.AnchorStore`, and segments the text into stable
spans. Segmentation is deterministic (paragraph boundaries) so the same source
always yields the same anchors, which keeps evidence citations reproducible
(SRS REQ-132). Imported content is treated as untrusted data and never executed
(SRS REQ-163).
"""

from __future__ import annotations

import hashlib
import re

from nw_engine.contracts.models import EvidenceAnchor
from nw_engine.provenance import AnchorStore


class SourceIngestor:
    """Ingests and freezes source editions.

    :ivar anchors: the shared :class:`AnchorStore` that holds frozen editions
        and pins.
    """

    def __init__(self, anchors: AnchorStore | None = None) -> None:
        self.anchors = anchors or AnchorStore()

    @staticmethod
    def fingerprint(text: str) -> str:
        """Return a content fingerprint for a source edition.

        :param text: the raw source text.
        :returns: a hex SHA-256 digest; identical content yields an identical
            fingerprint so re-import is detectable (SRS REQ-091).
        """

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def ingest(self, edition_id: str, text: str) -> list[EvidenceAnchor]:
        """Freeze an edition and segment it into addressable spans.

        :param edition_id: the edition's stable id.
        :param text: the raw source text.
        :returns: one :class:`EvidenceAnchor` per non-empty paragraph span, in
            document order. The edition is frozen; the content is never mutated.
        """

        fp = self.fingerprint(text)
        self.anchors.freeze_edition(edition_id, fp)
        spans = [s for s in re.split(r"\n\s*\n", text.strip()) if s.strip()]
        anchors: list[EvidenceAnchor] = []
        for i, _span in enumerate(spans):
            anchor = EvidenceAnchor(
                id=f"{edition_id}:span{i}",
                source_edition_id=edition_id,
                region=f"span{i}",
                fingerprint=fp,
            )
            self.anchors.add_anchor(anchor)
            anchors.append(anchor)
        return anchors
