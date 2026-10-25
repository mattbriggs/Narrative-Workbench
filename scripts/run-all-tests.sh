#!/usr/bin/env bash
# Run every test suite and the token test, printing coverage for each layer.
# Cloud-safe: builds and tests the Rust and Python parts and the headless JS;
# it does NOT open the Tauri desktop window (verified by the user on macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

echo "== Tokens: build + token test =="
node "$ROOT/design-tokens/build-tokens.mjs"
node "$ROOT/app/ui/tools/token-test.mjs"

echo "== Engine (Python): pytest + coverage =="
cd "$ROOT/engine"
PYTHONPATH=src "$VENV/bin/python" -m pytest --cov=nw_engine --cov-report=term-missing --cov-fail-under=90 -q

echo "== Contract: regenerate schema =="
cd "$ROOT"
PYTHONPATH="$ROOT/engine/src" "$VENV/bin/python" scripts/gen-contract.py

echo "== App (Rust): cargo llvm-cov =="
cd "$ROOT/app/src-tauri"
cargo llvm-cov --summary-only

echo "== UI (JS): node --test + coverage =="
cd "$ROOT/app/ui"
node --test --experimental-test-coverage "state/store.test.mjs" "statecharts/statecharts.test.mjs"

echo "== UI computed-style suite (wide / medium / narrow) =="
cd "$ROOT"
node app/ui/tools/run-computed-style.mjs

echo "== UI scenarios + screenshots (headless Chromium) =="
cd "$ROOT"
node app/ui/tools/run-scenarios.mjs "${NW_SHOT_DIR:-$ROOT/.screenshots}"

echo "All suites passed."
