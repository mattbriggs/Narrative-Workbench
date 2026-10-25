"""Integration tests for the RPC dispatcher (SRS REQ-160, mutation boundary)."""

from nw_engine.contracts.rpc import Request
from nw_engine.rpc import Dispatcher


def test_validate_op():
    d = Dispatcher()
    req = Request(op="validate", op_id="o1", payload={"disclosures": [{"fact": "x", "becomes_public": True}]})
    resp = d.handle(req)
    assert resp.ok
    assert resp.result["validation"]["passed"] is False


def test_generate_candidates_op_returns_proposals_only():
    d = Dispatcher()
    req = Request(op="generate_candidates", op_id="o2", payload={"target": "reconcile"})
    resp = d.handle(req)
    assert resp.ok
    cands = resp.result["candidates"]
    assert len(cands) == 2
    # Advisory: candidates carry validation but nothing is committed.
    assert all("validation" in c for c in cands)


def test_ingest_then_extract_pipeline():
    d = Dispatcher()
    ing = d.handle(Request(op="ingest_source", op_id="o3", payload={"edition_id": "ed1", "text": "One.\n\nTwo."}))
    assert ing.ok and len(ing.result["anchors"]) == 2
    ext = d.handle(Request(op="extract_observations", op_id="o4", payload={"edition_id": "ed2", "text": "One.\n\nTwo."}))
    assert ext.ok
    assert all(p["origin"] == "model_proposal" for p in ext.result["proposals"])
    assert all(p["payload"]["interpretation"]["accepted"] is False for p in ext.result["proposals"])


def test_unknown_op_is_structured_error():
    d = Dispatcher()
    resp = d.handle(Request(op="nope", op_id="o5"))
    assert resp.ok is False
    assert resp.error.code == "UNHANDLED_EVENT"


def test_engine_error_becomes_structured_error():
    d = Dispatcher()
    d.handle(Request(op="ingest_source", op_id="o6", payload={"edition_id": "edZ", "text": "First.\n\nSecond."}))
    # Re-ingesting changed content under the same edition raises SourceImmutableError.
    resp = d.handle(Request(op="ingest_source", op_id="o7", payload={"edition_id": "edZ", "text": "First.\n\nChanged."}))
    assert resp.ok is False
    assert resp.error.code == "SOURCE_IMMUTABLE"
    assert resp.error.scope == "edZ"
