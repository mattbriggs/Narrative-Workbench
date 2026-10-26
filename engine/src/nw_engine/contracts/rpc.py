"""Request/response envelope for the line-delimited JSON contract.

The application layer sends a :class:`Request`; the engine returns a
:class:`Response`. The engine never persists canonical state, so a successful
response carries a proposal and/or validation result that the application layer
then commits (SRS REQ-160, REQ-076).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from nw_engine.contracts.models import Context


class Request(BaseModel):
    """An application-to-engine command envelope.

    :param op: the operation name dispatched by :mod:`nw_engine.rpc`.
    :param op_id: idempotency key echoed back on the response (SRS REQ-161).
    :param context: resolved work/branch/commit/mode/actor context.
    :param payload: operation-specific arguments.
    """

    op: str
    op_id: str
    context: Context = Field(default_factory=Context)
    payload: dict[str, Any] = Field(default_factory=dict)


class ResponseError(BaseModel):
    """A structured engine error (SRS SS3.4 error table)."""

    code: str
    message: str
    scope: Optional[str] = None


class Response(BaseModel):
    """An engine-to-application result envelope."""

    op_id: str
    ok: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: Optional[ResponseError] = None
