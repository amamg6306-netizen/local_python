from __future__ import annotations

import logging
import re

from flask import Flask, has_request_context, request


_SECRET_PATTERNS = (
    re.compile(r"rzp_(?:live|test)_[A-Za-z0-9_-]+", re.I),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"(?i)(secret|password|token|authorization|cookie)\s*[=:]\s*[^\s,;]+"),
)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        record.args = ()
        if has_request_context():
            record.render_request_id = (request.headers.get("Rndr-Id") or "-")[:128]
            record.cf_ray = (request.headers.get("CF-Ray") or "-")[:128]
        else:
            record.render_request_id = "-"
            record.cf_ray = "-"
        return True


def configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s render_id=%(render_request_id)s cf_ray=%(cf_ray)s %(message)s"
        )
    )
    handler.addFilter(RedactingFilter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO if app.config["APP_ENV"] == "production" else logging.DEBUG)
