from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request
from sqlalchemy import select

from extensions import db
from models.billing import Payment, Subscription
from services.auth_service import security_log
from services.billing_service import (
    cancel_payment,
    checkout_intent,
    configured_methods,
    create_checkout_intent,
    create_payment_for_intent,
    create_razorpay_order,
    plan_for_role,
    price_breakdown,
    razorpay_credentials,
    record_gateway_callback,
    submit_manual_reference,
)
from services.marketplace_service import current_subscription, page_window
from utils.auth import current_user, require_roles

bp = Blueprint("billing", __name__)


@bp.post("/billing/start.php")
@require_roles("provider", "business")
def start():
    user = current_user(); assert user is not None
    try:
        plan_id = int(request.form.get("plan_id", 0))
        if plan_id <= 0:
            raise ValueError("Please choose a valid plan.")
        plan = plan_for_role(plan_id, user.role)
        current = current_subscription(user.id)
        if current and current.plan == plan.code:
            raise ValueError("That is already your current plan.")
        price = price_breakdown(plan)
        if price["total_minor"] <= 0:
            raise ValueError("This plan does not require checkout.")
        token = create_checkout_intent(user, plan_id)
        return redirect(f"/billing/payment-method.php?token={token}", code=303)
    except (ValueError, TypeError) as exc:
        db.session.rollback(); flash(str(exc), "error")
        return redirect(f"/{'business' if user.role == 'business' else 'provider'}/subscription.php", code=303)


@bp.get("/billing/payment-method.php")
@require_roles("provider", "business")
def payment_method():
    user = current_user(); assert user is not None
    token = request.args.get("token", "")
    intent = checkout_intent(token, user.id)
    if not intent or intent.status != "selecting_method":
        flash("This checkout is unavailable or expired.", "error")
        return redirect(f"/{'business' if user.role == 'business' else 'provider'}/subscription.php", code=303)
    if intent.user_role != user.role:
        abort(403)
    methods = configured_methods(user.role, intent.currency)
    return render_template("billing/payment_method.html", page_title="Payment Method — LocalConnect", token=token, intent=intent, methods=methods)


@bp.post("/billing/select-method.php")
@require_roles("provider", "business")
def select_method():
    user = current_user(); assert user is not None
    token = request.form.get("token", "")
    try:
        method_id = int(request.form.get("method_id", 0))
        payment = create_payment_for_intent(token, user, method_id)
        if payment.payment_method_type_snapshot == "gateway":
            create_razorpay_order(payment.id)
            return redirect(f"/billing/gateway.php?token={token}", code=303)
        return redirect(f"/billing/manual.php?token={token}", code=303)
    except Exception as exc:
        db.session.rollback(); security_log("checkout_method_failed", user_id=user.id, error_class=type(exc).__name__)
        flash(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Payment setup failed.", "error")
        return redirect("/billing/history.php", code=303)


@bp.get("/billing/gateway.php")
@require_roles("provider", "business")
def gateway():
    user = current_user(); assert user is not None
    token = request.args.get("token", "")
    intent = checkout_intent(token, user.id)
    if not intent or intent.status != "pending_gateway" or not intent.payment_id:
        flash("Gateway checkout is unavailable.", "error"); return redirect("/billing/history.php", code=303)
    payment = db.session.get(Payment, intent.payment_id)
    if not payment or payment.user_id != user.id:
        abort(404)
    try:
        payment = create_razorpay_order(payment.id); creds = razorpay_credentials()
    except Exception as exc:
        flash(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Gateway checkout could not be prepared.", "error"); return redirect("/billing/history.php", code=303)
    if not payment.provider_order_id:
        flash("Gateway order is not ready.", "error"); return redirect("/billing/history.php", code=303)
    checkout = {
        "key": creds["key_id"], "amount": int(payment.amount * 100), "currency": payment.currency,
        "name": "LocalConnect", "description": f"{payment.plan_name_snapshot} subscription",
        "order_id": payment.provider_order_id,
        "prefill": {"name": user.name, "email": user.email, "contact": user.phone or ""},
        "theme": {"color": "#0d6efd"},
    }
    return render_template("billing/gateway.html", page_title="Secure Checkout — LocalConnect", token=token, payment=payment, checkout=checkout)


@bp.post("/billing/gateway-return.php")
@require_roles("provider", "business")
def gateway_return():
    user = current_user(); assert user is not None
    try:
        local_id = int(request.form.get("local_payment_id", 0)); payment = db.session.get(Payment, local_id)
        if not payment or payment.user_id != user.id: raise ValueError("Payment not found.")
        record_gateway_callback(local_id, request.form.get("razorpay_order_id", "")[:190], request.form.get("razorpay_payment_id", "")[:190], request.form.get("razorpay_signature", "")[:128])
        flash("Gateway callback verified. Your payment is awaiting signed webhook/server reconciliation before entitlement is activated.", "success")
    except Exception as exc:
        db.session.rollback(); security_log("gateway_return_failed", user_id=user.id, error_class=type(exc).__name__); flash(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Gateway callback could not be verified.", "error")
    return redirect("/billing/history.php", code=303)


@bp.route("/billing/manual.php", methods=["GET", "POST"])
@require_roles("provider", "business")
def manual():
    user = current_user(); assert user is not None
    token = request.args.get("token") or request.form.get("token") or ""; intent = checkout_intent(token, user.id)
    if not intent or intent.status != "pending_manual" or not intent.payment_id:
        flash("Manual checkout is unavailable.", "error"); return redirect("/billing/history.php", code=303)
    payment = db.session.get(Payment, intent.payment_id)
    if not payment or payment.user_id != user.id or payment.payment_method_type_snapshot not in {"upi", "bank_transfer"}:
        abort(404)
    error = ""
    if request.method == "POST":
        try:
            submit_manual_reference(payment.id, user, request.form.get("payer_reference", ""), request.form.get("payer_note", "")); flash("Transfer reference submitted. This does not activate the plan; an administrator must reconcile the merchant account first.", "success"); return redirect("/billing/history.php", code=303)
        except (ValueError, RuntimeError) as exc:
            db.session.rollback(); error = str(exc)
    return render_template("billing/manual.html", page_title="Manual Payment — LocalConnect", token=token, payment=payment, error=error)


@bp.get("/billing/history.php")
@require_roles("provider", "business")
def history():
    user = current_user(); assert user is not None
    page, per, offset = page_window(20, 20)
    rows = db.session.execute(
        select(Payment, Subscription.status.label("subscription_status"), Subscription.starts_at, Subscription.ends_at)
        .outerjoin(Subscription, Subscription.id == Payment.subscription_id)
        .where(Payment.user_id == user.id)
        .order_by(Payment.id.desc()).limit(per + 1).offset(offset)
    ).all()
    has_next = len(rows) > per; rows = rows[:per]
    return render_template("billing/history.html", page_title="Billing history — LocalConnect", rows=rows, page=page, has_next=has_next, role=user.role)


@bp.post("/billing/cancel.php")
@require_roles("provider", "business")
def cancel():
    user = current_user(); assert user is not None
    try:
        payment_id = int(request.form.get("payment_id", 0));
        if payment_id <= 0: raise ValueError("Invalid payment.")
        flash(cancel_payment(payment_id, user), "success")
    except (ValueError, RuntimeError, TypeError) as exc:
        db.session.rollback(); flash(str(exc), "error")
    return redirect("/billing/history.php", code=303)
