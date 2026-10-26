"""Source ingestion for Criticism Parlor.

Fingerprints a source edition, freezes it, and segments it into stable
addressable spans without changing content (SRS REQ-050/051). Ingestion
produces evidence anchors (pins) into the frozen edition.
"""

from nw_engine.sources.ingest import SourceIngestor

__all__ = ["SourceIngestor"]
