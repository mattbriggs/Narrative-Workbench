"""Projection and analysis engine.

Builds derived views from committed history: counterfactual comparison matrices
(SRS REQ-063), timelines, and diffs. Projections are rebuildable and never
become authoritative narrative state (SRS REQ-099).
"""

from nw_engine.projections.comparison import ComparisonBuilder, DIMENSIONS
from nw_engine.projections.timeline import build_timeline

__all__ = ["ComparisonBuilder", "DIMENSIONS", "build_timeline"]
