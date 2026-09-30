from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Return healthy only when the web process and primary database are usable."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check database probe failed")
        db.session.rollback()
        return jsonify(status="error"), 503
    return jsonify(status="ok"), 200
