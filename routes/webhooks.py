from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from extensions import csrf, db
from services.auth_service import security_log
from services.billing_service import process_razorpay_webhook

bp = Blueprint("webhooks", __name__)


@bp.post("/webhooks/razorpay.php")
@csrf.exempt
def razorpay_webhook():
    # Server-to-server endpoint. Browser CSRF is intentionally not used; Razorpay
    # authenticates the exact raw body with X-Razorpay-Signature.
    raw = request.get_data(cache=False, as_text=False)
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("X-Razorpay-Event-Id", "") or None
    try:
        result = process_razorpay_webhook(raw, signature, event_id)
        return jsonify(ok=True, duplicate=bool(result.get("duplicate"))), 200
    except (ValueError, PermissionError) as exc:
        db.session.rollback()
        security_log("razorpay_webhook_rejected", error_class=type(exc).__name__)
        return jsonify(ok=False), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Razorpay webhook processing failed")
        security_log("razorpay_webhook_rejected", error_class=type(exc).__name__)
        return jsonify(ok=False), 500
