"""The AI gateway boundary.

All probabilistic assistance passes through this gateway, which produces typed
*proposals only* and never mutates canonical state (SRS SS3.10). The gateway
enforces the prohibited-authority rules (SRS REQ-101 to REQ-105) and attaches
provider metadata and fingerprints to every proposal.
"""

from nw_engine.ai.gateway import AIGateway, Planner, ReferencePlanner

__all__ = ["AIGateway", "Planner", "ReferencePlanner"]
