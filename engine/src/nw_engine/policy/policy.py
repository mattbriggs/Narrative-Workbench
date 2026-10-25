"""Workspace policy, provider governance, audit log, and plugin registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from nw_engine.errors import AuthorityDeniedError

#: Actions that MUST be audited (SRS NFR-024).
AUDITED_ACTIONS = frozenset(
    {"export", "share", "merge", "source_replacement", "policy_change", "archival"}
)

#: Capabilities a plugin may never declare (SRS NFR-050).
_FORBIDDEN_CAPABILITIES = frozenset(
    {"overwrite_source", "bypass_authority", "overwrite_history", "change_policy"}
)


class WorkspacePolicy:
    """Least-privilege capability policy and provider governance.

    :param local_only: when true, no external provider is allowed (SRS NFR-023).
    :param provider_allowlist: approved provider ids; empty means none approved.
    """

    def __init__(self, local_only: bool = False, provider_allowlist: set[str] | None = None) -> None:
        self.local_only = local_only
        self._allowlist = set(provider_allowlist or set())
        self._grants: dict[str, set[str]] = {}

    def grant(self, role: str, capability: str) -> None:
        """Grant a capability to a role within this workspace."""

        self._grants.setdefault(role, set()).add(capability)

    def can(self, role: str, capability: str) -> bool:
        """Return whether a role has a capability (least privilege: default no)."""

        return capability in self._grants.get(role, set())

    def require(self, role: str, capability: str) -> None:
        """Raise unless a role has a capability.

        :raises AuthorityDeniedError: when the capability is not granted.
        """

        if not self.can(role, capability):
            raise AuthorityDeniedError(f"{role} lacks capability {capability!r}", scope=capability)

    def provider_allowed(self, provider: str) -> bool:
        """Return whether a model provider may be used under this policy."""

        if self.local_only:
            return provider == "local"
        return provider in self._allowlist

    @staticmethod
    def redact(prompt: str, secrets: list[str]) -> str:
        """Redact secret substrings from a prompt before it leaves the boundary."""

        out = prompt
        for s in secrets:
            if s:
                out = out.replace(s, "[REDACTED]")
        return out


@dataclass
class AuditEntry:
    """A single append-only audit record."""

    action: str
    actor: str
    detail: str


class AuditLog:
    """Append-only audit log for mandated actions (SRS NFR-024)."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, action: str, actor: str, detail: str = "") -> None:
        """Append an audit entry.

        :raises ValueError: if a mandated-category name is misspelled is not
            enforced here; any action is recordable, but callers SHOULD use the
            :data:`AUDITED_ACTIONS` names for the mandated categories.
        """

        self._entries.append(AuditEntry(action=action, actor=actor, detail=detail))

    def entries(self) -> list[AuditEntry]:
        """Return a copy of the audit entries in order."""

        return list(self._entries)

    def covers(self, action: str) -> bool:
        """Return whether at least one entry records the given action."""

        return any(e.action == action for e in self._entries)


@dataclass
class Plugin:
    """A registered extension and its declared capabilities."""

    name: str
    kind: str  # lens | framework | operator | validator | provider | export
    capabilities: set[str] = field(default_factory=set)


class PluginRegistry:
    """Registers plugins that cannot bypass source immutability or authority."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin.

        :raises AuthorityDeniedError: if the plugin declares a forbidden
            capability (SRS NFR-050).
        """

        bad = plugin.capabilities & _FORBIDDEN_CAPABILITIES
        if bad:
            raise AuthorityDeniedError(
                f"plugin {plugin.name} declares forbidden capabilities {sorted(bad)}",
                scope=plugin.name,
            )
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Plugin:
        """Return a registered plugin by name."""

        return self._plugins[name]
