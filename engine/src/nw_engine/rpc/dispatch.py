"""Request dispatch to engine services.

The :class:`Dispatcher` owns shared engine services and routes an operation to a
handler. It is the integration surface the Tauri application layer drives over
stdio. Handlers return typed results; engine errors become structured error
responses carrying the error code and scope (SRS SS3.4).
"""

from __future__ import annotations

import logging
from typing import Callable

from nw_engine.ai import AIGateway, ReferencePlanner
from nw_engine.contracts.rpc import Request, Response, ResponseError
from nw_engine.errors import EngineError
from nw_engine.sources import SourceIngestor
from nw_engine.transitions import TrajectoryGenerator
from nw_engine.validation import ValidationEngine

logger = logging.getLogger(__name__)


class Dispatcher:
    """Routes requests to engine services (proposal-only; never commits)."""

    def __init__(self) -> None:
        self._validator = ValidationEngine()
        self._gateway = AIGateway(ReferencePlanner())
        self._ingestor = SourceIngestor()
        self._generator = TrajectoryGenerator(self._gateway, self._validator)
        self._handlers: dict[str, Callable[[dict], dict]] = {
            "validate": self._op_validate,
            "generate_candidates": self._op_generate,
            "ingest_source": self._op_ingest,
            "extract_observations": self._op_extract,
        }

    def handle(self, request: Request) -> Response:
        """Dispatch one request and return a response envelope.

        :param request: the parsed :class:`Request`.
        :returns: a :class:`Response`; ``ok`` is false with a structured error
            for an unknown op or any :class:`EngineError`.
        """

        handler = self._handlers.get(request.op)
        if handler is None:
            return Response(
                op_id=request.op_id,
                ok=False,
                error=ResponseError(code="UNHANDLED_EVENT", message=f"unknown op {request.op!r}"),
            )
        try:
            result = handler(request.payload)
        except EngineError as exc:
            return Response(
                op_id=request.op_id,
                ok=False,
                error=ResponseError(code=exc.code, message=exc.message, scope=exc.scope),
            )
        return Response(op_id=request.op_id, ok=True, result=result)

    # -- handlers ----------------------------------------------------------

    def _op_validate(self, payload: dict) -> dict:
        return {"validation": self._validator.validate(payload).model_dump()}

    def _op_generate(self, payload: dict) -> dict:
        target = payload["target"]
        candidates = self._generator.generate(target, payload.get("payloads"))
        return {"candidates": [c.model_dump() for c in candidates]}

    def _op_ingest(self, payload: dict) -> dict:
        anchors = self._ingestor.ingest(payload["edition_id"], payload["text"])
        return {"anchors": [a.model_dump() for a in anchors]}

    def _op_extract(self, payload: dict) -> dict:
        anchors = self._ingestor.ingest(payload["edition_id"], payload["text"])
        proposals = self._gateway.extract_observations(anchors)
        return {"proposals": [p.model_dump() for p in proposals]}
