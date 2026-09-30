from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from flask import current_app, request
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.billing import (
    CheckoutIntent,
    FeaturedListing,
    LeadWallet,
    ManualPaymentSubmission,
    Payment,
    PaymentMethod,
    PaymentMethodAudit,
    PaymentReconciliationJob,
    PaymentStatusHistory,
    PaymentWebhookEvent,
    Subscription,
    SubscriptionPlan,
)
from models.core import User
from services.auth_service import clean_text, client_ip, log_activity, security_log
from services.marketplace_service import create_notification, money_decimal, money_minor

SUPPORTED_GATEWAYS = {"razorpay": ("PAYMENT_RAZORPAY_KEY_ID", "PAYMENT_RAZORPAY_KEY_SECRET", "PAYMENT_RAZORPAY_WEBHOOK_SECRET")}
UPI_RE = re.compile(r"^[A-Za-z0-9._-]{2,128}@[A-Za-z0-9._-]{2,64}$")
REF_RE = re.compile(r"^[A-Za-z0-9_-]{5,190}$")
HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class PaymentGatewayError(RuntimeError):
    def __init__(self, message: str, *, ambiguous: bool = False, http_status: int | None = None):
        super().__init__(message)
        self.ambiguous = ambiguous
        self.http_status = http_status


def normalize_currency(value: object) -> str:
    currency = clean_text(value, 3, True, "Currency").upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Currency must be a 3-letter ISO code.")
    if currency != "INR":
        raise ValueError("Only INR is supported by the current subscription catalogue.")
    return currency


def valid_upi_id(value: str) -> bool:
    return bool(UPI_RE.fullmatch(value.strip()))


def gateway_config_status(code: str) -> dict:
    required = SUPPORTED_GATEWAYS.get(code)
    if not required:
        return {"configured": False, "summary": "Unsupported gateway", "missing": []}
    missing = []
    for name in required:
        value = str(current_app.config.get(name, "") or "").strip()
        if not value or "REPLACE_WITH_" in value:
            missing.append(name)
    key_id = str(current_app.config.get("PAYMENT_RAZORPAY_KEY_ID", "") or "")
    if code == "razorpay" and key_id.startswith("rzp_live_") and not current_app.config.get("PAYMENT_ALLOW_LIVE", False):
        missing.append("PAYMENT_ALLOW_LIVE")
    return {"configured": not missing, "summary": "Gateway environment configured" if not missing else "Gateway environment incomplete", "missing": missing}


def payment_method_config_status(method: PaymentMethod | dict) -> dict:
    def get(name, default=None):
        return method.get(name, default) if isinstance(method, dict) else getattr(method, name, default)
    kind = str(get("method_type", ""))
    if kind == "gateway":
        return gateway_config_status(str(get("gateway_code", "")))
    if kind == "upi":
        ok = valid_upi_id(str(get("merchant_upi_id", "") or "")) and bool(str(get("display_instructions", "") or "").strip())
        return {"configured": ok, "summary": "Manual UPI instructions configured" if ok else "UPI ID/instructions incomplete", "missing": []}
    if kind == "bank_transfer":
        ok = bool(str(get("bank_beneficiary", "") or "").strip()) and bool(str(get("display_instructions", "") or "").strip())
        return {"configured": ok, "summary": "Bank transfer instructions configured" if ok else "Beneficiary/instructions incomplete", "missing": []}
    return {"configured": False, "summary": "Unsupported payment method type", "missing": []}


def payment_method_snapshot(method: PaymentMethod) -> dict:
    keys = ("id", "code", "name", "method_type", "gateway_code", "audience", "currency", "merchant_upi_id", "bank_beneficiary", "bank_reference", "display_instructions", "display_order", "is_active")
    return {key: getattr(method, key) for key in keys}


def record_method_audit(method_id: int, admin_id: int, action: str, before: dict | None, after: dict | None) -> None:
    if action not in {"create", "update", "activate", "deactivate", "reorder"}:
        action = "update"
    db.session.add(PaymentMethodAudit(payment_method_id=method_id, admin_user_id=admin_id, action=action, before_json=before, after_json=after))


def plan_for_role(plan_id: int, role: str) -> SubscriptionPlan:
    if role not in {"provider", "business"}:
        raise ValueError("This account cannot purchase subscriptions.")
    plan = db.session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_active == 1, SubscriptionPlan.audience.in_([role, "both"])).limit(1))
    if not plan:
        raise ValueError("The selected plan is unavailable for this account.")
    return plan


def price_breakdown(plan: SubscriptionPlan) -> dict:
    subtotal = money_minor(plan.price_monthly)
    bps = max(0, min(10000, int(plan.tax_rate_bps or 0)))
    tax = int((Decimal(subtotal) * Decimal(bps) / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {
        "currency": "INR",
        "subtotal_minor": subtotal,
        "tax_minor": tax,
        "total_minor": subtotal + tax,
        "subtotal": money_decimal(subtotal),
        "tax": money_decimal(tax),
        "total": money_decimal(subtotal + tax),
        "tax_label": plan.tax_label or "Tax",
        "billing_period_months": max(1, min(24, int(plan.billing_period_months or 1))),
    }


def checkout_token_hash(token: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{64}", token or ""):
        return hashlib.sha256(b"invalid-token").hexdigest()
    return hashlib.sha256(token.encode()).hexdigest()


def create_checkout_intent(user: User, plan_id: int) -> str:
    plan = plan_for_role(plan_id, user.role)
    pricing = price_breakdown(plan)
    if pricing["total_minor"] <= 0:
        raise ValueError("The selected plan does not require payment.")
    token = secrets.token_hex(32)
    ttl = max(300, min(7200, int(current_app.config.get("PAYMENT_CHECKOUT_TTL_SECONDS", 1800))))
    row = CheckoutIntent(
        token_hash=checkout_token_hash(token), user_id=user.id, user_role=user.role, plan_id=plan.id,
        plan_code_snapshot=plan.code, plan_name_snapshot=plan.name, currency="INR",
        subtotal_amount=pricing["subtotal"], tax_amount=pricing["tax"], total_amount=pricing["total"],
        billing_period_months=pricing["billing_period_months"], status="selecting_method",
        expires_at=datetime.now() + timedelta(seconds=ttl),
    )
    db.session.add(row); db.session.commit()
    return token


def expire_checkout_intents(user_id: int) -> None:
    now = datetime.now()
    db.session.execute(
        update(CheckoutIntent)
        .where(
            CheckoutIntent.user_id == user_id,
            CheckoutIntent.status.in_(["selecting_method", "pending_gateway", "pending_manual"]),
            CheckoutIntent.expires_at < now,
        )
        .values(status="expired")
    )
    db.session.commit()


def checkout_intent(token: str, user_id: int, *, lock: bool = False) -> CheckoutIntent | None:
    if not re.fullmatch(r"[a-f0-9]{64}", token or ""):
        return None
    expire_checkout_intents(user_id)
    stmt = select(CheckoutIntent).where(CheckoutIntent.token_hash == checkout_token_hash(token), CheckoutIntent.user_id == user_id).limit(1)
    if lock:
        stmt = stmt.with_for_update()
    return db.session.scalar(stmt)


def configured_methods(role: str, currency: str = "INR") -> list[PaymentMethod]:
    if role not in {"provider", "business"}:
        return []
    rows = db.session.scalars(select(PaymentMethod).where(PaymentMethod.is_active == 1, PaymentMethod.currency == currency, PaymentMethod.audience.in_([role, "both"])).order_by(PaymentMethod.display_order, PaymentMethod.id)).all()
    return [row for row in rows if payment_method_config_status(row)["configured"]]


def add_payment_history(payment_id: int, old: str | None, new: str, source: str, event_key: str | None = None, note: str | None = None, actor_id: int | None = None) -> None:
    if source not in {"checkout", "callback", "webhook", "reconciliation", "admin", "system"}:
        source = "system"
    db.session.add(PaymentStatusHistory(payment_id=payment_id, old_status=old, new_status=new, source=source, external_event_key=event_key, note=(note or "")[:500] or None, actor_user_id=actor_id))


def create_payment_for_intent(token: str, user: User, method_id: int) -> Payment:
    try:
        intent = checkout_intent(token, int(user.id), lock=True)
        if not intent or intent.status != "selecting_method" or intent.expires_at < datetime.now():
            raise ValueError("This checkout is no longer available. Start again from the subscription page.")
        if intent.user_role != user.role:
            raise ValueError("Checkout role mismatch.")
        method = db.session.scalar(select(PaymentMethod).where(PaymentMethod.id == method_id, PaymentMethod.is_active == 1, PaymentMethod.currency == intent.currency, PaymentMethod.audience.in_([user.role, "both"])).with_for_update().limit(1))
        if not method or not payment_method_config_status(method)["configured"]:
            raise ValueError("That payment method is not available for this account.")
        payment = Payment(
            user_id=user.id, plan_id=intent.plan_id, payment_method_id=method.id,
            payment_method_code_snapshot=method.code, payment_method_name_snapshot=method.name,
            payment_method_type_snapshot=method.method_type, manual_instructions_snapshot=method.display_instructions,
            merchant_upi_id_snapshot=method.merchant_upi_id, bank_beneficiary_snapshot=method.bank_beneficiary,
            bank_reference_snapshot=method.bank_reference, plan_code_snapshot=intent.plan_code_snapshot,
            plan_name_snapshot=intent.plan_name_snapshot, subtotal_amount=intent.subtotal_amount,
            tax_amount=intent.tax_amount, billing_period_months=intent.billing_period_months,
            idempotency_key=secrets.token_hex(32), provider=method.gateway_code if method.method_type == "gateway" else "manual",
            amount=intent.total_amount, currency=intent.currency, status="pending", reconciliation_status="pending",
            checkout_expires_at=intent.expires_at,
        )
        db.session.add(payment); db.session.flush()
        intent.payment_id = payment.id
        intent.status = "pending_gateway" if method.method_type == "gateway" else "pending_manual"
        add_payment_history(payment.id, None, "pending", "checkout", note="Payment created from immutable checkout snapshot.", actor_id=user.id)
        db.session.commit()
        return payment
    except Exception:
        db.session.rollback(); raise


def razorpay_credentials() -> dict:
    key_id = str(current_app.config.get("PAYMENT_RAZORPAY_KEY_ID", "") or "").strip()
    secret = str(current_app.config.get("PAYMENT_RAZORPAY_KEY_SECRET", "") or "").strip()
    webhook = str(current_app.config.get("PAYMENT_RAZORPAY_WEBHOOK_SECRET", "") or "").strip()
    if not key_id or not secret or not webhook or any("REPLACE_WITH_" in x for x in (key_id, secret, webhook)):
        raise ValueError("Razorpay sandbox credentials are not configured.")
    if key_id.startswith("rzp_live_") and not current_app.config.get("PAYMENT_ALLOW_LIVE", False):
        raise ValueError("Live payment credentials are disabled by deployment policy. Use Razorpay Test Mode credentials.")
    return {"key_id": key_id, "key_secret": secret, "webhook_secret": webhook}


def razorpay_api(method: str, path: str, payload: dict | None = None) -> dict:
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", path):
        raise ValueError("Invalid gateway API path.")
    creds = razorpay_credentials()
    data = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
    req = urllib.request.Request("https://api.razorpay.com/v1" + path, data=data, method=method.upper())
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    auth = base64.b64encode(f"{creds['key_id']}:{creds['key_secret']}".encode()).decode()
    req.add_header("Authorization", "Basic " + auth)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            max_response_bytes = 1_048_576
            raw = response.read(max_response_bytes + 1)
            if len(raw) > max_response_bytes:
                raise PaymentGatewayError("Payment gateway response exceeded the safe size limit.", ambiguous=True)
            status = response.status
    except urllib.error.HTTPError as exc:
        if exc.code >= 500:
            raise PaymentGatewayError("The payment gateway is temporarily unavailable. The transaction needs reconciliation before retry.", ambiguous=True, http_status=exc.code) from exc
        raise PaymentGatewayError("The payment gateway rejected the request.", http_status=exc.code) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PaymentGatewayError("The payment gateway could not be reached. The transaction was not retried automatically because the remote result may be unknown.", ambiguous=True) from exc
    if not 200 <= status < 300:
        raise PaymentGatewayError("The payment gateway rejected the request.", http_status=status)
    try:
        decoded = json.loads(raw.decode() or "{}")
    except (ValueError, UnicodeDecodeError) as exc:
        raise PaymentGatewayError("Payment gateway response was invalid.", ambiguous=True) from exc
    return decoded if isinstance(decoded, dict) else {}


def create_razorpay_order(payment_id: int) -> Payment:
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise ValueError("Payment not found.")
    if payment.provider != "razorpay" or payment.payment_method_type_snapshot != "gateway":
        raise ValueError("This payment is not a Razorpay gateway payment.")
    if payment.provider_order_id:
        return payment
    minor = money_minor(payment.amount)
    payload = {"amount": minor, "currency": payment.currency, "receipt": f"lc_pmt_{payment.id}", "notes": {"localconnect_payment_id": str(payment.id), "localconnect_user_id": str(payment.user_id), "plan": payment.plan_code_snapshot or ""}}
    try:
        order = razorpay_api("POST", "/orders", payload)
    except PaymentGatewayError as exc:
        old = payment.status
        if exc.ambiguous:
            payment.status = "requires_review"; payment.reconciliation_status = "manual_review"; payment.reconciliation_note = "Gateway order result is ambiguous; reconcile before retry."
            add_payment_history(payment.id, old, "requires_review", "reconciliation", note="Gateway order result ambiguous.")
        else:
            payment.status = "failed"; payment.reconciliation_status = "warning"; payment.reconciliation_note = "Gateway rejected order creation."; payment.failed_at = datetime.now()
            add_payment_history(payment.id, old, "failed", "checkout", note="Gateway rejected order creation.")
        db.session.commit(); raise
    if str(order.get("id", "")) == "" or int(order.get("amount", -1)) != minor or str(order.get("currency", "")) != payment.currency or str(order.get("receipt", "")) != f"lc_pmt_{payment.id}":
        payment.status = "requires_review"; payment.reconciliation_status = "manual_review"; payment.reconciliation_note = "Gateway order response did not match local payment snapshot."
        add_payment_history(payment.id, "pending", "requires_review", "reconciliation", note=payment.reconciliation_note)
        db.session.commit()
        raise PaymentGatewayError("Gateway order response did not match the local payment snapshot.", ambiguous=True)
    payment.provider_order_id = str(order["id"]); payment.reconciliation_status = "pending"; db.session.commit(); return payment


def verify_callback_signature(order_id: str, payment_id: str, signature: str) -> bool:
    if not order_id or not payment_id or not HEX64_RE.fullmatch(signature or ""):
        return False
    secret = razorpay_credentials()["key_secret"]
    expected = hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.lower())


def record_gateway_callback(local_payment_id: int, provider_order_id: str, provider_payment_id: str, signature: str) -> None:
    try:
        payment = db.session.scalar(select(Payment).where(Payment.id == local_payment_id).with_for_update())
        if not payment:
            raise ValueError("Payment not found.")
        if payment.provider_order_id != provider_order_id:
            raise ValueError("Order mismatch.")
        if not verify_callback_signature(provider_order_id, provider_payment_id, signature):
            raise ValueError("Payment callback signature is invalid.")
        if payment.provider_payment_id and not hmac.compare_digest(payment.provider_payment_id, provider_payment_id):
            raise ValueError("Payment reference mismatch.")
        payment.provider_payment_id = provider_payment_id
        payment.gateway_callback_verified_at = payment.gateway_callback_verified_at or datetime.now()
        add_payment_history(payment.id, payment.status, payment.status, "callback", note="Signed browser callback verified; entitlement still waits for signed webhook + server reconciliation.", actor_id=payment.user_id)
        db.session.commit()
    except Exception:
        db.session.rollback(); raise


def _add_months(dt: datetime, months: int) -> datetime:
    months = max(1, min(24, months)); month = dt.month - 1 + months; year = dt.year + month // 12; month = month % 12 + 1
    import calendar
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def activate_entitlement(payment_id: int, source: str = "webhook", event_key: str | None = None) -> int:
    try:
        payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
        if not payment or payment.status != "paid":
            raise ValueError("Only a reconciled paid payment can activate entitlement.")
        if payment.subscription_id:
            db.session.commit()
            return int(payment.subscription_id)
        plan = db.session.get(SubscriptionPlan, payment.plan_id)
        user = db.session.scalar(select(User).where(User.id == payment.user_id).with_for_update())
        if not plan or not user:
            raise ValueError("Subscription plan or user not found.")
        now = datetime.now(); period = max(1, int(payment.billing_period_months or 1))
        subs = db.session.scalars(select(Subscription).where(Subscription.user_id == payment.user_id, Subscription.status.in_(["active", "scheduled"])).with_for_update()).all()
        same = [s for s in subs if s.plan == payment.plan_code_snapshot and s.ends_at and s.ends_at > now]
        if same:
            latest = max(same, key=lambda s: s.ends_at); start = latest.ends_at; status = "scheduled"
        else:
            start = now; status = "active"
            for sub in subs:
                if sub.status == "active" and sub not in same:
                    sub.status = "expired"; sub.ends_at = min(sub.ends_at or now, now)
        end = _add_months(start, period); invoice = f"LC-{now.year}-{payment.id:08d}"
        sub = Subscription(user_id=payment.user_id, plan=payment.plan_code_snapshot, plan_id=payment.plan_id, source_payment_id=payment.id, billing_period_months=period, status=status, starts_at=start, ends_at=end, price=payment.amount, invoice_reference=invoice)
        db.session.add(sub); db.session.flush()
        payment.subscription_id = sub.id; payment.invoice_reference = invoice
        intent = db.session.scalar(select(CheckoutIntent).where(CheckoutIntent.payment_id == payment.id).limit(1))
        if intent: intent.status = "paid"
        if int(plan.featured_days or 0) > 0:
            db.session.add(FeaturedListing(user_id=payment.user_id, subscription_id=sub.id, status="active" if status == "active" else "pending", starts_at=start, ends_at=start + timedelta(days=int(plan.featured_days))))
        if status == "active" and plan.lead_limit is not None:
            wallet = db.session.get(LeadWallet, payment.user_id)
            if wallet: wallet.credits = int(wallet.credits or 0) + int(plan.lead_limit)
            else: db.session.add(LeadWallet(user_id=payment.user_id, credits=int(plan.lead_limit)))
            sub.benefits_applied_at = datetime.now()
        create_notification(payment.user_id, "subscription", "Subscription activated", "Your paid renewal is scheduled after the current entitlement ends." if status == "scheduled" else "Your paid subscription is now active.", "billing/history.php")
        log_activity(payment.user_id, "subscription_entitlement_created", "subscription", sub.id, f"payment_id={payment.id};source={source}")
        db.session.commit(); return int(sub.id)
    except Exception:
        db.session.rollback(); raise


def mark_payment_paid(payment_id: int, source: str = "reconciliation", event_key: str | None = None, actor_id: int | None = None) -> None:
    payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment:
        raise ValueError("Payment not found.")
    if payment.status in {"refunded", "disputed"}:
        raise ValueError("A refunded/disputed payment cannot be reactivated automatically.")
    old = payment.status
    if old != "paid":
        payment.status = "paid"
        payment.reconciliation_status = "matched"
        payment.reconciliation_note = None
        payment.paid_at = payment.paid_at or datetime.now()
        payment.failed_at = None
        add_payment_history(payment.id, old, "paid", source, event_key, "Verified server-side reconciliation matched amount, currency and order.", actor_id)
    # activate_entitlement commits the payment transition and entitlement as one
    # database transaction; if entitlement creation fails, both roll back.
    activate_entitlement(payment.id, source, event_key)


def remote_payment(payment_id: str) -> dict:
    if not REF_RE.fullmatch(payment_id): raise ValueError("Invalid provider payment id.")
    return razorpay_api("GET", "/payments/" + payment_id)


def remote_order(order_id: str) -> dict:
    if not REF_RE.fullmatch(order_id): raise ValueError("Invalid provider order id.")
    return razorpay_api("GET", "/orders/" + order_id)


def reconcile_razorpay(payment_id: int, source: str = "reconciliation", event_key: str | None = None, actor_id: int | None = None) -> None:
    p = db.session.get(Payment, payment_id)
    if not p or p.provider != "razorpay" or not p.provider_order_id or not p.provider_payment_id:
        raise ValueError("Gateway payment references are incomplete.")
    rp = remote_payment(p.provider_payment_id); ro = remote_order(p.provider_order_id); expected = money_minor(p.amount); issues = []
    checks = [
        (str(rp.get("id", "")) == p.provider_payment_id, "payment id mismatch"),
        (str(rp.get("order_id", "")) == p.provider_order_id, "order id mismatch"),
        (int(rp.get("amount", -1)) == expected, "payment amount mismatch"),
        (str(rp.get("currency", "")) == p.currency, "payment currency mismatch"),
        (str(rp.get("status", "")) == "captured", "payment is not captured"),
        (str(ro.get("id", "")) == p.provider_order_id, "remote order id mismatch"),
        (int(ro.get("amount", -1)) == expected, "order amount mismatch"),
        (str(ro.get("currency", "")) == p.currency, "order currency mismatch"),
        (str(ro.get("receipt", "")) == f"lc_pmt_{p.id}", "order receipt mismatch"),
    ]
    issues = [message for ok, message in checks if not ok]
    if issues:
        old = p.status; p.status = "requires_review"; p.reconciliation_status = "warning"; p.reconciliation_note = "; ".join(issues)[:500]
        add_payment_history(p.id, old, "requires_review", source, event_key, p.reconciliation_note, actor_id); db.session.commit()
        raise ValueError("Gateway reconciliation did not match the local payment snapshot.")
    mark_payment_paid(p.id, source, event_key, actor_id)


def submit_manual_reference(payment_id: int, user: User, reference: str, note: str) -> None:
    reference = clean_text(reference, 190, True, "Payment reference"); note = clean_text(note, 500, False, "Note")
    p = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not p or int(p.user_id) != int(user.id): raise ValueError("Payment not found.")
    if p.payment_method_type_snapshot not in {"upi", "bank_transfer"} or p.status != "pending": raise ValueError("This manual payment is not awaiting a reference.")
    m = db.session.scalar(select(ManualPaymentSubmission).where(ManualPaymentSubmission.payment_id == payment_id).with_for_update())
    if m:
        if m.status != "pending": raise ValueError("This manual payment has already been reviewed.")
        m.payer_reference = reference; m.payer_note = note or None
    else:
        db.session.add(ManualPaymentSubmission(payment_id=p.id, user_id=user.id, payer_reference=reference, payer_note=note or None, status="pending"))
    p.reconciliation_status = "manual_review"; p.reconciliation_note = "Manual transfer submitted; admin bank/UPI reconciliation required."
    add_payment_history(p.id, "pending", "pending", "checkout", note="Manual payment reference submitted; this is not proof of payment.", actor_id=user.id)
    db.session.commit()


def verify_manual_payment(payment_id: int, admin_id: int, approved: bool, note: str) -> None:
    note = clean_text(note, 500, True, "Review note")
    p = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update()); m = db.session.scalar(select(ManualPaymentSubmission).where(ManualPaymentSubmission.payment_id == payment_id).with_for_update())
    if not p: raise ValueError("Payment not found.")
    if not m or m.status != "pending": raise ValueError("No pending manual payment submission exists.")
    m.status = "verified" if approved else "rejected"; m.reviewed_by = admin_id; m.review_note = note; m.reviewed_at = datetime.now(); old = p.status
    if approved:
        p.status = "paid"; p.reconciliation_status = "matched"; p.reconciliation_note = "Manual transfer verified by authorized admin against external merchant account."; p.paid_at = p.paid_at or datetime.now()
        add_payment_history(p.id, old, "paid", "admin", note="Manual payment externally reconciled and approved.", actor_id=admin_id)
    else:
        p.status = "failed"; p.reconciliation_status = "matched"; p.reconciliation_note = "Manual payment submission rejected after reconciliation."; p.failed_at = datetime.now()
        add_payment_history(p.id, old, "failed", "admin", note="Manual payment submission rejected.", actor_id=admin_id)
        intent = db.session.scalar(select(CheckoutIntent).where(CheckoutIntent.payment_id == p.id).limit(1))
        if intent: intent.status = "failed"
    log_activity(admin_id, "manual_payment_verified" if approved else "manual_payment_rejected", "payment", p.id, "Manual reconciliation decision recorded.")
    if approved:
        # Keep manual verification and entitlement activation atomic so a paid
        # manual payment cannot be stranded without its subscription.
        activate_entitlement(p.id, "admin")
    else:
        db.session.commit()


def cancel_payment(payment_id: int, user: User) -> str:
    p = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not p or int(p.user_id) != int(user.id): raise ValueError("Payment not found.")
    if p.status not in {"pending", "requires_review"}: raise ValueError("This payment can no longer be cancelled from checkout.")
    manual = db.session.scalar(select(ManualPaymentSubmission).where(ManualPaymentSubmission.payment_id == p.id).limit(1))
    has_external = bool(p.provider_order_id or p.provider_payment_id or manual)
    old = p.status; intent = db.session.scalar(select(CheckoutIntent).where(CheckoutIntent.payment_id == p.id).limit(1))
    if intent: intent.status = "cancelled"
    if not has_external:
        p.status = "cancelled"; p.reconciliation_status = "matched"; p.reconciliation_note = "Cancelled before any external payment reference existed."; p.cancelled_at = datetime.now()
        add_payment_history(p.id, old, "cancelled", "checkout", note="Checkout cancelled before an external payment reference existed.", actor_id=user.id)
        message = "Checkout cancelled. No external payment reference had been created."
    else:
        p.status = "requires_review"; p.reconciliation_status = "manual_review"; p.reconciliation_note = "User stopped checkout after an external reference/submission existed; reconcile before treating it as cancelled."
        add_payment_history(p.id, old, "requires_review", "checkout", note="Checkout stopped, but external payment state may still change; reconciliation required.", actor_id=user.id)
        message = "Checkout stopped. Because an external order/reference already exists, the payment remains under reconciliation and is not assumed cancelled."
    db.session.commit(); return message



def mark_payment_failed(payment_id: int, source: str, event_key: str | None = None, note: str = "Payment failed.") -> None:
    payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment:
        return
    if payment.status in {"paid", "refunded", "partially_refunded", "disputed"}:
        db.session.commit()
        return
    old = payment.status
    payment.status = "failed"
    payment.reconciliation_status = "matched"
    payment.reconciliation_note = note[:500]
    payment.failed_at = payment.failed_at or datetime.now()
    intent = db.session.scalar(select(CheckoutIntent).where(CheckoutIntent.payment_id == payment.id).limit(1))
    if intent:
        intent.status = "failed"
    add_payment_history(payment.id, old, "failed", source, event_key, note)
    db.session.commit()


def revoke_entitlement(payment_id: int, reason: str) -> None:
    payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment or not payment.subscription_id:
        db.session.commit()
        return
    sub = db.session.scalar(select(Subscription).where(Subscription.id == payment.subscription_id).with_for_update())
    if sub and sub.status in {"active", "scheduled", "suspended"}:
        sub.status = "cancelled"
        sub.suspension_reason = reason[:255]
    db.session.commit()


def mark_refund_state(payment_id: int, amount_refunded_minor: int, event_key: str) -> None:
    payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment:
        db.session.commit()
        return
    total_minor = money_minor(payment.amount)
    full = int(amount_refunded_minor) >= total_minor
    new_status = "refunded" if full else "partially_refunded"
    old = payment.status
    payment.status = new_status
    payment.reconciliation_status = "matched" if full else "manual_review"
    payment.reconciliation_note = "Full refund verified from gateway." if full else "Partial refund requires entitlement review."
    if full:
        payment.refunded_at = payment.refunded_at or datetime.now()
    add_payment_history(payment.id, old, new_status, "webhook", event_key, "Full refund processed." if full else "Partial refund processed; entitlement retained pending review.")
    db.session.commit()
    if full:
        revoke_entitlement(payment.id, "Payment fully refunded.")


def mark_disputed(payment_id: int, event_key: str, note: str = "Gateway dispute opened.") -> None:
    payment = db.session.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment:
        db.session.commit()
        return
    old = payment.status
    payment.status = "disputed"
    payment.reconciliation_status = "manual_review"
    payment.reconciliation_note = note[:500]
    payment.disputed_at = payment.disputed_at or datetime.now()
    add_payment_history(payment.id, old, "disputed", "webhook", event_key, note)
    if payment.subscription_id:
        sub = db.session.scalar(select(Subscription).where(Subscription.id == payment.subscription_id).with_for_update())
        if sub and sub.status in {"active", "scheduled"}:
            sub.status = "suspended"
            sub.suspension_reason = "Payment dispute requires review."
    db.session.commit()


def find_local_payment_by_provider_refs(provider_payment_id: str, provider_order_id: str) -> Payment | None:
    if provider_payment_id:
        row = db.session.scalar(select(Payment).where(Payment.provider == "razorpay", Payment.provider_payment_id == provider_payment_id).limit(1))
        if row:
            return row
    if provider_order_id:
        return db.session.scalar(select(Payment).where(Payment.provider == "razorpay", Payment.provider_order_id == provider_order_id).limit(1))
    return None


def enqueue_reconciliation_job(payment_id: int | None, webhook_event_id: int, reason: str) -> bool:
    if webhook_event_id <= 0:
        return False
    queue_max = max(100, min(100000, int(current_app.config.get("PAYMENT_RECONCILIATION_QUEUE_MAX", 10000))))
    max_attempts = max(1, min(10, int(current_app.config.get("PAYMENT_WORKER_MAX_ATTEMPTS", 5))))
    try:
        active = int(db.session.scalar(select(func.count(PaymentReconciliationJob.id)).where(PaymentReconciliationJob.status.in_(["queued", "processing", "retry"]))) or 0)
        if active >= queue_max:
            security_log("payment_reconciliation_queue_full", active_jobs=active, queue_max=queue_max)
            return False
        existing = db.session.scalar(select(PaymentReconciliationJob).where(PaymentReconciliationJob.webhook_event_id == webhook_event_id).limit(1))
        if existing:
            if existing.payment_id is None and payment_id:
                existing.payment_id = payment_id
            existing.last_error = reason[:500]
            if existing.status == "dead" and existing.attempts < existing.max_attempts:
                existing.status = "retry"
                existing.next_attempt_at = datetime.now()
            db.session.commit()
            return True
        db.session.add(PaymentReconciliationJob(webhook_event_id=webhook_event_id, payment_id=payment_id, status="queued", attempts=0, max_attempts=max_attempts, next_attempt_at=datetime.now(), last_error=reason[:500]))
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return bool(db.session.scalar(select(PaymentReconciliationJob.id).where(PaymentReconciliationJob.webhook_event_id == webhook_event_id).limit(1)))
    except Exception as exc:
        db.session.rollback()
        security_log("payment_reconciliation_enqueue_failed", event_id=webhook_event_id, error_class=type(exc).__name__)
        return False


def run_reconciliation_batch(requested_limit: int = 20) -> dict[str, int]:
    limit = max(1, min(100, min(max(1, int(current_app.config.get("PAYMENT_WORKER_BATCH_MAX", 20))), int(requested_limit))))
    now = datetime.now()
    stale_before = now - timedelta(minutes=10)
    db.session.execute(
        update(PaymentReconciliationJob)
        .where(
            PaymentReconciliationJob.status == "processing",
            PaymentReconciliationJob.locked_at < stale_before,
            PaymentReconciliationJob.attempts < PaymentReconciliationJob.max_attempts,
        )
        .values(
            status="retry",
            locked_at=None,
            next_attempt_at=now,
            last_error="Recovered stale processing lease.",
        )
    )
    db.session.execute(
        update(PaymentReconciliationJob)
        .where(
            PaymentReconciliationJob.status.in_(["processing", "retry", "queued"]),
            PaymentReconciliationJob.attempts >= PaymentReconciliationJob.max_attempts,
        )
        .values(status="dead", locked_at=None)
    )
    db.session.commit()

    stats = {"claimed": 0, "done": 0, "retry": 0, "dead": 0}
    for _ in range(limit):
        job_id: int | None = None
        try:
            job = db.session.scalar(
                select(PaymentReconciliationJob)
                .where(PaymentReconciliationJob.status.in_(["queued", "retry"]), PaymentReconciliationJob.attempts < PaymentReconciliationJob.max_attempts, PaymentReconciliationJob.next_attempt_at <= datetime.now())
                .order_by(PaymentReconciliationJob.next_attempt_at, PaymentReconciliationJob.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not job:
                db.session.rollback()
                break
            job.status = "processing"; job.attempts = int(job.attempts or 0) + 1; job.locked_at = datetime.now()
            job_id = int(job.id)
            db.session.commit(); stats["claimed"] += 1

            job = db.session.get(PaymentReconciliationJob, job_id)
            event = db.session.get(PaymentWebhookEvent, job.webhook_event_id) if job and job.webhook_event_id else None
            if not job or not event:
                raise RuntimeError("Reconciliation job or webhook event disappeared.")
            payment_id = int(job.payment_id or 0)
            if payment_id <= 0:
                local = find_local_payment_by_provider_refs(event.provider_payment_id or "", event.provider_order_id or "")
                payment_id = int(local.id) if local else 0
                if payment_id:
                    job.payment_id = payment_id; db.session.commit()
            if payment_id <= 0:
                raise RuntimeError("No local payment matches this webhook yet.")
            event_key = f"queued:event:{event.id}"
            kind = event.event_type or ""
            if kind == "payment.captured":
                reconcile_razorpay(payment_id, "reconciliation", event_key)
            elif kind == "payment.failed":
                mark_payment_failed(payment_id, "reconciliation", event_key, "Queued reconciliation confirmed payment.failed.")
            elif kind.startswith("refund."):
                if not event.provider_payment_id:
                    raise RuntimeError("Refund event has no provider payment reference.")
                remote = remote_payment(event.provider_payment_id)
                mark_refund_state(payment_id, int(remote.get("amount_refunded", 0)), event_key)
            elif "dispute" in kind:
                mark_disputed(payment_id, event_key, "Queued reconciliation processed gateway dispute event.")
            job = db.session.get(PaymentReconciliationJob, job_id)
            job.status = "done"; job.locked_at = None; job.last_error = None
            if event.processing_status == "failed":
                event.processing_status = "processed"; event.processing_note = "Recovered by bounded reconciliation worker."; event.processed_at = datetime.now()
            db.session.commit(); stats["done"] += 1
        except Exception as exc:
            db.session.rollback()
            try:
                job = db.session.get(PaymentReconciliationJob, job_id) if job_id is not None else None
                if job:
                    dead = int(job.attempts or 0) >= int(job.max_attempts or 1)
                    job.status = "dead" if dead else "retry"; job.locked_at = None; job.last_error = str(exc)[:500]
                    if not dead:
                        backoff = min(3600, 30 * (2 ** max(0, int(job.attempts or 1) - 1)))
                        job.next_attempt_at = datetime.now() + timedelta(seconds=backoff)
                    db.session.commit(); stats["dead" if dead else "retry"] += 1
                    security_log("payment_reconciliation_job_failed", job_id=job.id, error_class=type(exc).__name__, dead=dead)
            except Exception:
                db.session.rollback()
                security_log("payment_reconciliation_worker_state_failed", error_class=type(exc).__name__)
    return stats


def process_razorpay_webhook(raw_body: bytes, signature: str, event_id: str | None = None) -> dict:
    if len(raw_body) > 1_048_576:
        raise ValueError("Webhook payload is too large.")
    allowed = tuple(current_app.config.get("PAYMENT_RAZORPAY_WEBHOOK_IP_ALLOWLIST") or ())
    if allowed and client_ip() not in allowed:
        raise PermissionError("Webhook source is not allowed.")
    if not HEX64_RE.fullmatch(signature or ""):
        raise ValueError("Invalid webhook signature.")
    secret = razorpay_credentials()["webhook_secret"]
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.lower()):
        raise ValueError("Invalid webhook signature.")
    try:
        event = json.loads(raw_body.decode())
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid webhook JSON.") from exc
    if not isinstance(event, dict):
        raise ValueError("Invalid webhook JSON.")
    kind = str(event.get("event", ""))
    if not kind or len(kind) > 120:
        raise ValueError("Webhook event type is invalid.")
    payload = event.get("payload", {}) or {}
    pentity = ((payload.get("payment") or {}).get("entity") or {})
    rentity = ((payload.get("refund") or {}).get("entity") or {})
    dentity = ((payload.get("dispute") or {}).get("entity") or {})
    provider_payment_id = str(pentity.get("id") or rentity.get("payment_id") or dentity.get("payment_id") or "")
    provider_order_id = str(pentity.get("order_id") or "")
    header_key = (event_id or "").strip()
    key = header_key[:190] if header_key and len(header_key) <= 190 else hashlib.sha256(raw_body).hexdigest()
    digest = hashlib.sha256(raw_body).hexdigest()
    existing = db.session.scalar(select(PaymentWebhookEvent).where(PaymentWebhookEvent.provider == "razorpay", PaymentWebhookEvent.event_key == key).limit(1))
    if existing:
        if existing.processing_status == "failed":
            local = find_local_payment_by_provider_refs(existing.provider_payment_id or "", existing.provider_order_id or "")
            if not enqueue_reconciliation_job(int(local.id) if local else None, int(existing.id), "Gateway retried a previously failed webhook event."):
                raise RuntimeError("Reconciliation queue is unavailable or full.")
        return {"duplicate": True, "processed": existing.processing_status == "processed", "event_key": key}
    row = PaymentWebhookEvent(provider="razorpay", event_key=key, event_type=kind, payload_sha256=digest, provider_payment_id=provider_payment_id or None, provider_order_id=provider_order_id or None, signature_valid=1, processing_status="received")
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = db.session.scalar(select(PaymentWebhookEvent).where(PaymentWebhookEvent.provider == "razorpay", PaymentWebhookEvent.event_key == key).limit(1))
        return {"duplicate": True, "processed": bool(existing and existing.processing_status == "processed"), "event_key": key}
    try:
        local = find_local_payment_by_provider_refs(provider_payment_id, provider_order_id)
        if local and provider_payment_id and not local.provider_payment_id:
            local.provider_payment_id = provider_payment_id; db.session.commit()
        status, note = "ignored", "Event recorded; no local action required."
        if kind == "payment.captured":
            if not local:
                raise ValueError("No local payment matches captured gateway references.")
            reconcile_razorpay(local.id, "webhook", key); status, note = "processed", "Captured payment reconciled and entitlement processed."
        elif kind == "payment.failed":
            if local:
                mark_payment_failed(local.id, "webhook", key, "Gateway reported payment.failed."); status, note = "processed", "Failed payment recorded."
            else:
                note = "No local payment matched failed event."
        elif kind.startswith("refund."):
            if local:
                if not provider_payment_id:
                    raise ValueError("Refund event has no provider payment reference.")
                remote = remote_payment(provider_payment_id)
                mark_refund_state(local.id, int(remote.get("amount_refunded", 0)), key); status, note = "processed", "Refund state reconciled from gateway payment."
            else:
                note = "No local payment matched refund event."
        elif "dispute" in kind:
            if local:
                mark_disputed(local.id, key, f"Gateway dispute event: {kind}"); status, note = "processed", "Dispute recorded and entitlement suspended pending review."
            else:
                note = "No local payment matched dispute event."
        row = db.session.get(PaymentWebhookEvent, row.id); row.processing_status = status; row.processing_note = note[:500]; row.processed_at = datetime.now(); db.session.commit()
        return {"duplicate": False, "processed": status == "processed", "event_key": key, "note": note}
    except Exception as exc:
        db.session.rollback()
        row = db.session.get(PaymentWebhookEvent, row.id); row.processing_status = "failed"; row.processing_note = str(exc)[:500]; row.processed_at = datetime.now(); db.session.commit()
        local = find_local_payment_by_provider_refs(provider_payment_id, provider_order_id)
        enqueue_reconciliation_job(int(local.id) if local else None, int(row.id), str(exc))
        security_log("payment_webhook_processing_failed", event_type=kind, event_key=key, error_class=type(exc).__name__)
        raise

