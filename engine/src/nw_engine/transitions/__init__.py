"""Candidate generation, soft-goal scoring, and prose reconciliation.

Produces candidate ordinary and model-level transitions, keeps rejected
alternatives, scores soft goals separately from validity (SRS REQ-079), and
detects facts introduced by prose edits (SRS REQ-047/048).
"""

from nw_engine.transitions.generator import TrajectoryGenerator
from nw_engine.transitions.reconcile import ProseReconciler, ReconciliationProposal

__all__ = ["TrajectoryGenerator", "ProseReconciler", "ReconciliationProposal"]
