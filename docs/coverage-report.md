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

## Phase 3 — Scene composition

Engine modules added: candidate trajectory generation (validates each
candidate, scores soft goals separately from validity, preserves divergent
alternatives, forbid creates a gate proposal and preserves the candidate) and
prose reconciliation (detects prose assertions absent from the model and lets
the author choose language or model authority; never mutates silently). The
semantic conflict resolver path is exercised via the repository (Phase 1).

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python, cumulative) | 93 | 99% line / 98% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% (unchanged) | ≥ 80% | PASS |
| UI (JS) | 14 | 100% (unchanged) | states covered | PASS |

## Phase 4 — Multiscale architecture

Engine modules added: versioned structural frameworks with a registry that
evaluates one graph under several frameworks (unit-type and containment rules)
without duplication, and episode continuity contracts with mutation rules and
closure-driven state propagation into a shared ledger (restore persists
nothing; preserved invariants are never overwritten).

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python, cumulative) | 99 | 99% line / 98% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% (unchanged) | ≥ 80% | PASS |
| UI (JS) | 14 | 100% (unchanged) | states covered | PASS |

## Phase 5 — Experimental form

Engine modules added: the eight formal operators (INTERRUPT, RECURSE, REFRACT,
COLLAGE, SPIRAL, WITHHOLD, REINTERPRET, TRANSPOSE) as versioned, configurable
definitions that add formal relations and refuse to assert a diegetic CAUSES
edge; intentional-vs-accidental inconsistency classification; and reader-model
transitions that reclassify events without a causal edge.

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python, cumulative) | 106 | 99% line / 98% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% (unchanged) | ≥ 80% | PASS |
| UI (JS) | 14 | 100% (unchanged) | states covered | PASS |

## Phase 6 — Collaboration and ecosystem

Engine modules added: workspace policy (least privilege, default deny; provider
allowlist / local-only; prompt redaction), append-only audit log covering the
six mandated actions, a plugin registry that rejects authority-bypassing
capabilities, portable export (open JSON + Markdown report + source
fingerprints, lossy-projection warning), a derived-index store where deleting an
index never deletes the work, and the RPC dispatcher that ties validate /
generate / ingest / extract end to end and turns engine errors into structured
responses (never commits).

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python, cumulative) | 119 | 99% line (1101 stmts, 3 missed) / 98% branch | ≥ 90% | PASS |
| App (Rust) | 29 | 98.0% region / 97.6% line | ≥ 80% | PASS |
| UI (JS) | 14 | 100% line / 100% branch | states covered | PASS |

## Final summary (all phases)

| Layer | Tests | Coverage | Target | Result |
| --- | --- | --- | --- | --- |
| Engine (Python) | 119 | 99% line / 98% branch (invariant core 100%) | ≥ 90% | **PASS** |
| App (Rust) | 29 | 98.0% region / 97.6% line | ≥ 80% | **PASS** |
| UI (JS) | 14 | 100% line / 100% branch | states covered | **PASS** |
| Tokens | — | token test PASS (0 unresolved aliases; no literals) | pass | **PASS** |

**Total: 162 automated tests across three layers, all passing; every layer at
or above its coverage target.** Reproduce with `bash scripts/run-all-tests.sh`.

### Acceptance checks (spec §10)

| Check | Status | Note |
| --- | --- | --- |
| 1 Token / literal-value test | PASS | `app/ui/tools/token-test.mjs` |
| 2 Computed-style test | DEFERRED | needs packaged screens (CMP full build, Phase-1 UI subset done) |
| 3 Packaged screenshot comparison | DEFERRED | needs the packaged desktop app (user's Mac) |
| 4 Gherkin scenarios | PARTIAL | lifecycle/selection/job scenarios covered as unit + statechart tests; full screen scenarios pending the component build |
| 5 `[PRE]` confirmation (all 20) | OPEN | all 20 remain Proposed; owners must sign off (`docs/pre-register.md`) |

The deterministic core (engine) and application/UI logic are fully built and
covered in the cloud. The full CMP-01..18 DOM components, the five packaged
screens, and the desktop screenshot gate are the remaining UI build and are
verified on the user's Mac; they do not change the coverage above.
