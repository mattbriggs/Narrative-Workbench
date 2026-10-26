"""Narrative Workbench engine sidecar.

The engine owns the typed narrative graph (NetworkX), deterministic validation,
proposal generation, and projections. It never persists canonical state: it
returns typed proposals and validation results, and the application layer
performs the atomic commit (SRS REQ-076, REQ-077).

Package layout mirrors the SRS domain model (SRS SS6) and the implementation
plan's layer model:

- :mod:`nw_engine.contracts` -- Pydantic boundary models (requests, responses,
  proposals, validation results).
- :mod:`nw_engine.domain` -- fixed vocabulary and enumerations.
- :mod:`nw_engine.graph` -- the NetworkX graph kernel.
- :mod:`nw_engine.modal` -- modal models and model transitions.
- :mod:`nw_engine.validation` -- hard invariants and soft-goal scoring.
- :mod:`nw_engine.transitions` -- candidate generation and reconciliation.
- :mod:`nw_engine.provenance` -- provenance records and evidence anchors.
- :mod:`nw_engine.repository` -- append-only operations, commits, branches.
- :mod:`nw_engine.projections` -- timelines, diffs, comparison matrices.
- :mod:`nw_engine.frameworks` -- structural frameworks and formal operators.
- :mod:`nw_engine.ai` -- the proposal-only AI gateway boundary.
- :mod:`nw_engine.rpc` -- line-delimited JSON dispatch.
"""

__version__ = "0.1.0"
