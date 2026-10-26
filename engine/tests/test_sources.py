"""Tests for source ingestion and segmentation (SRS REQ-050/051/091)."""

import pytest

from nw_engine.errors import SourceImmutableError
from nw_engine.sources import SourceIngestor


def test_ingest_segments_and_freezes():
    ing = SourceIngestor()
    text = "First paragraph.\n\nSecond paragraph.\n\n\nThird."
    anchors = ing.ingest("ed1", text)
    assert [a.region for a in anchors] == ["span0", "span1", "span2"]
    assert all(ing.anchors.resolves(a.id) for a in anchors)


def test_fingerprint_is_stable_and_content_sensitive():
    assert SourceIngestor.fingerprint("abc") == SourceIngestor.fingerprint("abc")
    assert SourceIngestor.fingerprint("abc") != SourceIngestor.fingerprint("abd")


def test_reingesting_changed_content_under_same_edition_is_rejected():
    ing = SourceIngestor()
    ing.ingest("ed1", "Para one.\n\nPara two.")
    with pytest.raises(SourceImmutableError):
        ing.ingest("ed1", "Para one.\n\nParagraph two changed.")
