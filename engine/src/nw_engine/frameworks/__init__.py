"""Structural frameworks and episode contracts.

A structural framework defines permitted unit types, containment relations,
milestones, hard constraints, soft goals, and projections, and is versioned
independently so the same graph can be evaluated under several frameworks
(SRS REQ-031). Episode contracts declare inherited state, allowed mutations,
preserved invariants, exit effects, and closure behavior (SRS REQ-033).
"""

from nw_engine.frameworks.episode import ClosureBehavior, EpisodeContract
from nw_engine.frameworks.framework import (
    FrameworkRegistry,
    FrameworkViolation,
    StructuralFramework,
)

__all__ = [
    "ClosureBehavior",
    "EpisodeContract",
    "FrameworkRegistry",
    "FrameworkViolation",
    "StructuralFramework",
]
