"""Criticism Parlor domain services.

Manages Observation/Finding/Claim assertions on interpretive branches, enforces
that an accepted assertion rests on resolved evidence (SRS REQ-053), and
compares competing models that share a frozen source edition (SRS REQ-056).
Accepting an assertion never relabels it as a source fact (SRS REQ-058).
"""

from nw_engine.criticism.interpretations import InterpretationStore

__all__ = ["InterpretationStore"]
