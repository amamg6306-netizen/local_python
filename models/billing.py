from __future__ import annotations

from extensions import db
from models.base import (
    BIGINT_UNSIGNED,
    INT_UNSIGNED,
    SMALLINT_UNSIGNED,
    TINYINT,
    TINYINT_UNSIGNED,
    TimestampMixin,
    enum_type,
    now_default,
)


class SubscriptionPlan(db.Model, TimestampMixin):
    __tablename__ = "subscription_plans"

    id = db.Column(INT_UNSIGNED, primary_key=True, autoincrement=True)
    code = db.Column(db.String(40), nullable=False, unique=True)
    name = db.Column(db.String(80), nullable=False)
    audience = db.Column(enum_type("subscription_plan_audience", "provider", "business", "both"), nullable=False, server_default="both")
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False, server_default="0")
    billing_period_months = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="1")
    tax_rate_bps = db.Column(SMALLINT_UNSIGNED, nullable=False, server_default="0")
    tax_label = db.Column(db.String(40), nullable=False, server_default="Tax")
    featured_days = db.Column(INT_UNSIGNED, nullable=False, server_default="0")
    lead_limit = db.Column(INT_UNSIGNED)
    description = db.Column(db.String(255))
    is_active = db.Column(TINYINT, nullable=False, server_default="1")


class Subscription(db.Model, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        db.UniqueConstraint("source_payment_id", name="uq_subscription_source_payment"),
        db.Index("idx_subscription_user", "user_id", "status"),
        db.Index("idx_subscription_schedule", "user_id", "status", "starts_at", "ends_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_subscription_user"), nullable=False)
    plan = db.Column(enum_type("subscription_legacy_plan", "free", "professional", "business"), nullable=False, server_default="free")
    plan_id = db.Column(INT_UNSIGNED, db.ForeignKey("subscription_plans.id", ondelete="RESTRICT", name="fk_subscription_plan"))
    source_payment_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payments.id", ondelete="RESTRICT", name="fk_subscription_source_payment"))
    billing_period_months = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="1")
    status = db.Column(enum_type("subscription_status", "active", "scheduled", "expired", "cancelled", "pending", "suspended"), nullable=False, server_default="active")
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    price = db.Column(db.Numeric(10, 2), nullable=False, server_default="0")
    invoice_reference = db.Column(db.String(80))
    suspension_reason = db.Column(db.String(255))
    benefits_applied_at = db.Column(db.DateTime)


class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"
    __table_args__ = (
        db.Index("idx_payment_method_active", "audience", "currency", "is_active", "display_order"),
        db.Index("idx_payment_method_type", "method_type", "gateway_code"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    code = db.Column(db.String(60), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    method_type = db.Column(enum_type("payment_method_type", "gateway", "upi", "bank_transfer"), nullable=False)
    gateway_code = db.Column(db.String(60))
    audience = db.Column(enum_type("payment_method_audience", "provider", "business", "both"), nullable=False, server_default="both")
    currency = db.Column(db.String(3), nullable=False, server_default="INR")
    merchant_upi_id = db.Column(db.String(190))
    bank_beneficiary = db.Column(db.String(160))
    bank_reference = db.Column(db.String(190))
    display_instructions = db.Column(db.String(2000))
    display_order = db.Column(INT_UNSIGNED, nullable=False, server_default="100")
    is_active = db.Column(TINYINT, nullable=False, server_default="0")
    created_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="RESTRICT", name="fk_payment_method_created_by"), nullable=False)
    updated_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="RESTRICT", name="fk_payment_method_updated_by"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), onupdate=now_default())


class Payment(db.Model, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        db.UniqueConstraint("idempotency_key", name="uq_payment_idempotency"),
        db.UniqueConstraint("provider", "provider_order_id", name="uq_payment_provider_order"),
        db.UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_payment"),
        db.Index("idx_payment_status", "status", "created_at"),
        db.Index("idx_payment_reconcile", "reconciliation_status", "status", "created_at"),
        db.Index("idx_payment_method", "payment_method_id", "status", "created_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_payment_user"), nullable=False)
    subscription_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("subscriptions.id", ondelete="SET NULL", name="fk_payment_sub"))
    plan_id = db.Column(INT_UNSIGNED, db.ForeignKey("subscription_plans.id", ondelete="RESTRICT", name="fk_payment_plan"))
    payment_method_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payment_methods.id", ondelete="SET NULL", name="fk_payment_method"))
    payment_method_code_snapshot = db.Column(db.String(60))
    payment_method_name_snapshot = db.Column(db.String(120))
    payment_method_type_snapshot = db.Column(db.String(40))
    manual_instructions_snapshot = db.Column(db.String(2000))
    merchant_upi_id_snapshot = db.Column(db.String(190))
    bank_beneficiary_snapshot = db.Column(db.String(160))
    bank_reference_snapshot = db.Column(db.String(190))
    plan_code_snapshot = db.Column(db.String(40))
    plan_name_snapshot = db.Column(db.String(80))
    subtotal_amount = db.Column(db.Numeric(10, 2))
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, server_default="0")
    billing_period_months = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="1")
    idempotency_key = db.Column(db.String(64))
    provider = db.Column(db.String(50))
    provider_order_id = db.Column(db.String(190))
    provider_payment_id = db.Column(db.String(190))
    gateway_callback_verified_at = db.Column(db.DateTime)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, server_default="INR")
    status = db.Column(enum_type("payment_status", "pending", "paid", "failed", "cancelled", "refunded", "partially_refunded", "disputed", "requires_review"), nullable=False, server_default="pending")
    reconciliation_status = db.Column(enum_type("payment_reconciliation_status", "pending", "matched", "warning", "manual_review"), nullable=False, server_default="pending")
    reconciliation_note = db.Column(db.String(500))
    paid_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    refunded_at = db.Column(db.DateTime)
    disputed_at = db.Column(db.DateTime)
    invoice_reference = db.Column(db.String(80))
    checkout_expires_at = db.Column(db.DateTime)


class PaymentMethodAudit(db.Model):
    __tablename__ = "payment_method_audit"
    __table_args__ = (
        db.Index("idx_pma_method", "payment_method_id", "created_at"),
        db.Index("idx_pma_admin", "admin_user_id", "created_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    payment_method_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payment_methods.id", ondelete="RESTRICT", name="fk_pma_method"), nullable=False)
    admin_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="RESTRICT", name="fk_pma_admin"), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    before_json = db.Column(db.JSON)
    after_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class CheckoutIntent(db.Model):
    __tablename__ = "checkout_intents"
    __table_args__ = (
        db.UniqueConstraint("token_hash", name="uq_checkout_token"),
        db.Index("idx_checkout_user", "user_id", "status", "expires_at"),
        db.Index("idx_checkout_plan", "plan_id", "status"),
        db.Index("idx_checkout_expiry", "status", "expires_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    token_hash = db.Column(db.String(64), nullable=False)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_checkout_user"), nullable=False)
    user_role = db.Column(enum_type("checkout_user_role", "provider", "business"), nullable=False)
    plan_id = db.Column(INT_UNSIGNED, db.ForeignKey("subscription_plans.id", ondelete="RESTRICT", name="fk_checkout_plan"), nullable=False)
    plan_code_snapshot = db.Column(db.String(40), nullable=False)
    plan_name_snapshot = db.Column(db.String(80), nullable=False)
    currency = db.Column(db.String(3), nullable=False, server_default="INR")
    subtotal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, server_default="0")
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    billing_period_months = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="1")
    status = db.Column(enum_type("checkout_status", "selecting_method", "pending_gateway", "pending_manual", "paid", "failed", "cancelled", "expired"), nullable=False, server_default="selecting_method")
    payment_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payments.id", ondelete="SET NULL", name="fk_checkout_payment"))
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), onupdate=now_default())


class PaymentStatusHistory(db.Model):
    __tablename__ = "payment_status_history"
    __table_args__ = (
        db.Index("idx_psh_payment", "payment_id", "created_at"),
        db.Index("idx_psh_external", "external_event_key"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    payment_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payments.id", ondelete="CASCADE", name="fk_psh_payment"), nullable=False)
    old_status = db.Column(db.String(40))
    new_status = db.Column(db.String(40), nullable=False)
    source = db.Column(enum_type("payment_status_source", "checkout", "callback", "webhook", "reconciliation", "admin", "system"), nullable=False)
    external_event_key = db.Column(db.String(190))
    note = db.Column(db.String(500))
    actor_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_psh_actor"))
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class PaymentWebhookEvent(db.Model):
    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        db.UniqueConstraint("provider", "event_key", name="uq_webhook_event"),
        db.Index("idx_webhook_payment", "provider_payment_id"),
        db.Index("idx_webhook_order", "provider_order_id"),
        db.Index("idx_webhook_status", "processing_status", "received_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    provider = db.Column(db.String(40), nullable=False)
    event_key = db.Column(db.String(190), nullable=False)
    event_type = db.Column(db.String(120), nullable=False)
    payload_sha256 = db.Column(db.String(64), nullable=False)
    provider_payment_id = db.Column(db.String(190))
    provider_order_id = db.Column(db.String(190))
    signature_valid = db.Column(TINYINT, nullable=False, server_default="0")
    processing_status = db.Column(enum_type("webhook_processing_status", "received", "processed", "ignored", "failed"), nullable=False, server_default="received")
    processing_note = db.Column(db.String(500))
    received_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    processed_at = db.Column(db.DateTime)


class ManualPaymentSubmission(db.Model):
    __tablename__ = "manual_payment_submissions"
    __table_args__ = (
        db.UniqueConstraint("payment_id", name="uq_manual_payment"),
        db.Index("idx_manual_status", "status", "submitted_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    payment_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payments.id", ondelete="CASCADE", name="fk_manual_payment"), nullable=False)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_manual_user"), nullable=False)
    payer_reference = db.Column(db.String(190), nullable=False)
    payer_note = db.Column(db.String(500))
    status = db.Column(enum_type("manual_payment_status", "pending", "verified", "rejected"), nullable=False, server_default="pending")
    reviewed_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_manual_reviewer"))
    review_note = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    reviewed_at = db.Column(db.DateTime)


class PaymentReconciliationJob(db.Model):
    __tablename__ = "payment_reconciliation_jobs"
    __table_args__ = (
        db.UniqueConstraint("webhook_event_id", name="uq_reconcile_webhook_event"),
        db.Index("idx_reconcile_due", "status", "next_attempt_at", "id"),
        db.Index("idx_reconcile_payment", "payment_id", "status"),
        db.Index("idx_reconcile_payment_due", "payment_id", "status", "next_attempt_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    webhook_event_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payment_webhook_events.id", ondelete="CASCADE", name="fk_reconcile_webhook"))
    payment_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("payments.id", ondelete="CASCADE", name="fk_reconcile_payment"))
    status = db.Column(enum_type("reconciliation_job_status", "queued", "processing", "retry", "done", "dead"), nullable=False, server_default="queued")
    attempts = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="0")
    max_attempts = db.Column(TINYINT_UNSIGNED, nullable=False, server_default="5")
    next_attempt_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    locked_at = db.Column(db.DateTime)
    last_error = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), onupdate=now_default())


class FeaturedListing(db.Model, TimestampMixin):
    __tablename__ = "featured_listings"
    __table_args__ = (db.Index("idx_featured", "status", "starts_at", "ends_at"),)

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_featured_user"), nullable=False)
    subscription_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("subscriptions.id", ondelete="SET NULL", name="fk_featured_sub"))
    status = db.Column(enum_type("featured_listing_status", "pending", "active", "expired", "cancelled"), nullable=False, server_default="pending")
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)


class LeadWallet(db.Model):
    __tablename__ = "lead_wallets"

    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_lead_wallet_user"), primary_key=True)
    credits = db.Column(INT_UNSIGNED, nullable=False, server_default="0")
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), onupdate=now_default())


class Advertisement(db.Model, TimestampMixin):
    __tablename__ = "advertisements"
    __table_args__ = (db.Index("idx_ads_status", "status", "starts_at", "ends_at"),)

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.String(500))
    image = db.Column(db.String(255))
    target_url = db.Column(db.String(255))
    placement = db.Column(db.String(80))
    budget = db.Column(db.Numeric(10, 2), nullable=False, server_default="0")
    impressions = db.Column(INT_UNSIGNED, nullable=False, server_default="0")
    clicks = db.Column(INT_UNSIGNED, nullable=False, server_default="0")
    status = db.Column(enum_type("advertisement_status", "draft", "active", "paused", "expired"), nullable=False, server_default="draft")
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    created_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="RESTRICT", name="fk_ad_admin"), nullable=False)
    sponsor_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_ad_sponsor"))
