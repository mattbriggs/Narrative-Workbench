"""Workspace policy, audit, and the plugin registry.

Applies least privilege by workspace, work, branch, and mode-sensitive action
(SRS NFR-021); governs provider access with allowlists, local-only workspaces,
and redaction (NFR-023); keeps an append-only audit record for export, share,
merge, source replacement, policy change, and archival (NFR-024); and registers
plugins that run with declared capabilities and cannot bypass source
immutability or mutation policy (NFR-050).
"""

from nw_engine.policy.policy import (
    AUDITED_ACTIONS,
    AuditLog,
    PluginRegistry,
    WorkspacePolicy,
)

__all__ = ["AUDITED_ACTIONS", "AuditLog", "PluginRegistry", "WorkspacePolicy"]
