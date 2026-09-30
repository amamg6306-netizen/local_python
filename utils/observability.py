from __future__ import annotations

import re
import time

from flask import Flask, g, request

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _header_id(name: str) -> str:
    value = (request.headers.get(name) or "").strip()
    return value if _REQUEST_ID_RE.fullmatch(value) else ""


def register_observability(app: Flask) -> None:
    @app.before_request
    def start_request_timer() -> None:
        g.request_started_at = time.perf_counter()
        g.render_request_id = _header_id("Rndr-Id")
        g.cf_ray = _header_id("CF-Ray")

    @app.after_request
    def record_request_metrics(response):
        started = getattr(g, "request_started_at", None)
        if started is None:
            return response
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        threshold = int(app.config.get("SLOW_REQUEST_MS", 1500))
        if elapsed_ms >= threshold and request.path != "/health":
            app.logger.warning(
                "slow_request method=%s path=%s status=%s duration_ms=%.1f",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
            )
        return response
