"""Tests for workspace policy, audit, plugins, and export (SRS SS3.12, NFR-020..025, 050)."""

import json

import pytest

from nw_engine.errors import AuthorityDeniedError
from nw_engine.export import DerivedIndexStore, ExportBuilder
from nw_engine.policy import AUDITED_ACTIONS, AuditLog, PluginRegistry, WorkspacePolicy
from nw_engine.policy.policy import Plugin


def test_least_privilege_defaults_to_no():
    p = WorkspacePolicy()
    assert p.can("reviewer", "commit_canonical") is False
    p.grant("narrative_designer", "commit_canonical")
    assert p.can("narrative_designer", "commit_canonical") is True
    with pytest.raises(AuthorityDeniedError):
        p.require("reviewer", "commit_canonical")
    p.require("narrative_designer", "commit_canonical")  # no raise


def test_provider_allowlist_and_local_only():
    p = WorkspacePolicy(provider_allowlist={"approved-llm"})
    assert p.provider_allowed("approved-llm") is True
    assert p.provider_allowed("random-llm") is False
    local = WorkspacePolicy(local_only=True, provider_allowlist={"approved-llm"})
    assert local.provider_allowed("approved-llm") is False
    assert local.provider_allowed("local") is True


def test_redaction():
    out = WorkspacePolicy.redact("key=SECRET123 and token=T", ["SECRET123", "T"])
    assert "SECRET123" not in out and "[REDACTED]" in out


def test_audit_log_covers_mandated_actions():
    log = AuditLog()
    for action in AUDITED_ACTIONS:
        log.record(action, actor="admin", detail="x")
    assert all(log.covers(a) for a in AUDITED_ACTIONS)
    assert len(log.entries()) == len(AUDITED_ACTIONS)


def test_plugin_cannot_bypass_authority():
    reg = PluginRegistry()
    reg.register(Plugin(name="mckee", kind="framework", capabilities={"project_hierarchy"}))
    assert reg.get("mckee").kind == "framework"
    with pytest.raises(AuthorityDeniedError):
        reg.register(Plugin(name="evil", kind="validator", capabilities={"overwrite_source"}))


def test_export_includes_fingerprints_and_warns_when_lossy():
    b = ExportBuilder("c42")
    b.add_json("model.json", {"units": 3})
    b.add_markdown_report("# Report\n")
    b.add_source_fingerprint("ed1", "fp-abc")
    pkg = b.build(lossy=True)
    assert pkg.source_commit == "c42"
    assert pkg.warnings and "lossy" in pkg.warnings[0]
    assert "report.md" in pkg.files
    fps = json.loads(pkg.files["source-fingerprints.json"])
    assert fps["ed1"] == "fp-abc"


def test_export_not_lossy_has_no_warning():
    pkg = ExportBuilder("c1").build()
    assert pkg.warnings == []


def test_deleting_index_preserves_work():
    store = DerivedIndexStore()
    store.add_work("work1")
    store.build_index("idx1", "work1")
    store.delete_index("idx1")
    assert store.work_exists("work1") is True
    store.delete_index("missing")  # no-op, no raise
