"""Structured JSON logging with a per-request id.

Application logs are emitted as one JSON object per line so they can be shipped
to any collector without a parsing rule per message. Set ``LOG_FORMAT=plain`` for
human-readable output during local development.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if os.getenv("LOG_FORMAT", "json").lower() == "plain":
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel((level or os.getenv("LOG_LEVEL", "INFO")).upper())

    # uvicorn installs its own handlers; route them through ours instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


class RequestContextMiddleware:
    """Pure-ASGI middleware: assigns a request id and logs method, path, status, duration."""

    def __init__(self, app) -> None:
        self.app = app
        self.logger = logging.getLogger("qeymatban.request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = scope["headers"] and dict(scope["headers"]).get(b"x-request-id")
        request_id = request_id.decode() if request_id else new_request_id()
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self.logger.info(
                "%s %s -> %s",
                scope.get("method"),
                scope.get("path"),
                status_code,
                extra={"extra_fields": {"status": status_code, "duration_ms": duration_ms}},
            )
            request_id_var.reset(token)
