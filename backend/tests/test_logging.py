"""Structured logging middleware: request id propagation and JSON output."""

import json
import logging

from fastapi.testclient import TestClient

from app.logging_config import JsonFormatter, configure_logging, request_id_var
from app.main import app


def test_request_id_is_echoed_and_logged(capsys):
    configure_logging("INFO")
    response = TestClient(app).get("/health", headers={"x-request-id": "abc123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "abc123"

    # The handler writes one JSON object per line to stdout; assert on the record
    # itself rather than on caplog, which configure_logging() deliberately replaces.
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    request_lines = [line for line in lines if line["logger"] == "qeymatban.request"]
    assert request_lines, "middleware did not log the request"
    assert request_lines[-1]["message"] == "GET /health -> 200"
    assert request_lines[-1]["request_id"] == "abc123"
    assert request_lines[-1]["status"] == 200
    assert "duration_ms" in request_lines[-1]


def test_request_id_is_generated_when_absent():
    response = TestClient(app).get("/health")

    assert response.headers["x-request-id"]
    assert len(response.headers["x-request-id"]) == 16


def test_json_formatter_emits_one_object_per_line():
    record = logging.LogRecord("qeymatban.test", logging.INFO, __file__, 1, "hello", None, None)
    record.extra_fields = {"duration_ms": 12.5}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["duration_ms"] == 12.5
    assert payload["request_id"] == request_id_var.get()
