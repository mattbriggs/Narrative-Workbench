"""Deterministic validation.

Enforces the seven hard-invariant categories and scores soft goals separately
from validity (SRS SS8.3, REQ-079). Validation is a pure function of its input
payload so results are reproducible from stored inputs and validator version
(SRS REQ-191).
"""

from nw_engine.validation.invariants import ValidationEngine

__all__ = ["ValidationEngine"]
