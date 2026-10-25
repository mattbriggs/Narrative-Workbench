# Coverage report (per phase)

Measured in the cloud session. The Python engine (deterministic core) is built
phase by phase; the Rust application layer and the JS UI core are Phase-1
infrastructure and are re-run each phase without change unless noted.

Tooling: `pytest --cov` (coverage.py, branch), `cargo llvm-cov`, and
`node --test --experimental-test-coverage`. Targets (implementation plan §7.2):
engine ≥ 90% (invariant core 100% branch), app ≥ 80%, JS every state/scenario.

> Cloud note: the Rust and Python parts and the headless JS are built and tested
> here. The Tauri desktop window is verified by the user on macOS; it is not
> claimed as checked in the cloud (`CLAUDE.md`).

## Phase 0 — Setup

- Token test: **PASS** (0 unresolved aliases; no literal visual values; role tokens only).
- No code coverage yet (scaffolding only).

## Phase 1 — Foundation

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python) | 60 | 99% line / 96% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% region / 97.6% line | ≥ 80% | PASS |
| UI (JS) | 14 | 100% line / 100% branch | states covered | PASS |

Modules delivered: graph kernel, typed edges, append-only repository, branch
lifecycle, semantic-conflict detection, provenance records, evidence anchors
(pins) + publication gate, hard-invariant validation + soft goals; Rust
proposal lifecycle, authority, repository port, provenance, engine-client
contract, commands; JS proposal/selection/job statecharts and observable store.

## Phase 2 — Critical laboratory

Engine modules added: source ingestion + fingerprint + segmentation, the
proposal-only AI gateway (prohibited-authority enforcement, extraction and
candidate proposals with model metadata), interpretive assertions
(Observation/Finding/Claim) with evidence-gated acceptance and competing-lens
comparison, the seven-dimension counterfactual comparison matrix (deterministic
vs. generated hypotheses; reader model = intended), the timeline projection, and
the event-driven job runner (partial never committed; linked retry).

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python, cumulative) | 88 | 99% line / 98% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% region / 97.6% line (unchanged) | ≥ 80% | PASS |
| UI (JS) | 14 | 100% (unchanged) | states covered | PASS |
