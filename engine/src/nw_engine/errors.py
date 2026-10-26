"""Engine error types.

These map to the boundary error codes in SRS SS3.4. Each carries a ``code`` and
optional ``scope`` so the application layer can surface a visible reason without
re-deriving it.
"""

from __future__ import annotations

from typing import Optional


class EngineError(Exception):
    """Base class for engine errors.

    :param message: human-readable explanation.
    :param code: stable boundary error code (SRS SS3.4).
    :param scope: optional subject the error applies to.
    """

    code = "ENGINE_ERROR"

    def __init__(self, message: str, *, scope: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.scope = scope


class GraphConstraintError(EngineError):
    """A typed-edge or identity constraint was violated (SRS REQ-013)."""

    code = "GRAPH_CONSTRAINT"


class SchemaInvalidError(EngineError):
    """A proposal payload was incomplete or malformed (SRS REQ-072)."""

    code = "SCHEMA_INVALID"


class HardInvariantError(EngineError):
    """A hard invariant failed (SRS REQ-074)."""

    code = "HARD_INVARIANT"


class AuthorityDeniedError(EngineError):
    """The actor lacks authority for the action (SRS REQ-080)."""

    code = "AUTHORITY_DENIED"


class SourceImmutableError(EngineError):
    """An attempt was made to mutate a frozen source edition (SRS REQ-051)."""

    code = "SOURCE_IMMUTABLE"


class AnchorBrokenError(EngineError):
    """An evidence anchor no longer resolves (SRS REQ-057)."""

    code = "ANCHOR_BROKEN"


class UnhandledEventError(EngineError):
    """No transition exists from the current state (SRS REQ-188)."""

    code = "UNHANDLED_EVENT"


class ParentChangedError(EngineError):
    """The commit parent moved after acceptance (SRS REQ-078)."""

    code = "PARENT_CHANGED"
