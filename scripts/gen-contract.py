#!/usr/bin/env python3
"""Emit a JSON Schema for the engine boundary contract.

Generates ``app/src-tauri/contract.schema.json`` from the Pydantic models so the
Rust ``serde`` mirror can be checked for drift in CI (implementation plan
SS3.2). Run with the engine's ``src`` on ``PYTHONPATH``:

    PYTHONPATH=engine/src python scripts/gen-contract.py

Exits 0 on success. Intended to be diffed against the committed schema; a
non-empty diff means the contract changed and both sides must be updated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from nw_engine.contracts.models import (
    Commit,
    Comparison,
    Context,
    Proposal,
    ValidationResult,
)
from nw_engine.contracts.rpc import Request, Response

MODELS = {
    "Context": Context,
    "Proposal": Proposal,
    "ValidationResult": ValidationResult,
    "Commit": Commit,
    "Comparison": Comparison,
    "Request": Request,
    "Response": Response,
}


def build_schema() -> dict:
    """Return a combined JSON Schema document for the contract models."""

    return {name: TypeAdapter(model).json_schema() for name, model in MODELS.items()}


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path("app/src-tauri/contract.schema.json")
    out.write_text(json.dumps(build_schema(), indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
