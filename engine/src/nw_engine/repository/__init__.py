"""Versioned narrative repository.

Stores append-only operations, immutable commits, and movable branch pointers
(SRS REQ-090 to REQ-099). Projections are rebuildable from committed history;
the repository never rewrites a parent commit and never silently deletes
accepted history.
"""

from nw_engine.repository.conflicts import SemanticConflict, detect_semantic_conflicts
from nw_engine.repository.repository import Repository

__all__ = ["Repository", "SemanticConflict", "detect_semantic_conflicts"]
