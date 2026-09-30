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


class ProviderProfile(db.Model, TimestampMixin):
    __tablename__ = "provider_profiles"
    __table_args__ = (
        db.Index("idx_provider_verify", "verification_status"),
        db.Index("idx_provider_available", "availability_status"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_provider_user"), nullable=False, unique=True)
    headline = db.Column(db.String(180))
    about = db.Column(db.Text)
    experience_years = db.Column(SMALLINT_UNSIGNED, server_default="0")
    service_area = db.Column(db.String(255))
    price_min = db.Column(db.Numeric(10, 2))
    price_max = db.Column(db.Numeric(10, 2))
    availability_status = db.Column(enum_type("provider_availability", "available", "busy", "unavailable"), nullable=False, server_default="available")
    working_hours = db.Column(db.String(255))
    verification_status = db.Column(enum_type("provider_verification", "pending", "verified", "rejected"), nullable=False, server_default="pending")
    verified_at = db.Column(db.DateTime)
    is_featured = db.Column(TINYINT, nullable=False, server_default="0")
    profile_views = db.Column(INT_UNSIGNED, nullable=False, server_default="0")


class BusinessProfile(db.Model, TimestampMixin):
    __tablename__ = "business_profiles"
    __table_args__ = (
        db.Index("idx_business_name", "business_name"),
        db.Index("idx_business_verify", "verification_status"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_business_user"), nullable=False, unique=True)
    category_id = db.Column(INT_UNSIGNED, db.ForeignKey("categories.id", ondelete="SET NULL", name="fk_business_category"))
    business_name = db.Column(db.String(180))
    slug = db.Column(db.String(200), unique=True)
    logo = db.Column(db.String(255))
    description = db.Column(db.Text)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(25))
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    price_min = db.Column(db.Numeric(10, 2))
    price_max = db.Column(db.Numeric(10, 2))
    website = db.Column(db.String(255))
    social_links = db.Column(db.JSON)
    verification_status = db.Column(enum_type("business_verification", "pending", "verified", "rejected"), nullable=False, server_default="pending")
    verified_at = db.Column(db.DateTime)
    is_featured = db.Column(TINYINT, nullable=False, server_default="0")
    profile_views = db.Column(INT_UNSIGNED, nullable=False, server_default="0")


class Service(db.Model, TimestampMixin):
    __tablename__ = "services"
    __table_args__ = (
        db.UniqueConstraint("category_id", "slug", name="uq_service_category_slug"),
        db.Index("idx_service_name", "name"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    category_id = db.Column(INT_UNSIGNED, db.ForeignKey("categories.id", ondelete="RESTRICT", name="fk_services_category"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(TINYINT, nullable=False, server_default="1")


class ProviderService(db.Model, TimestampMixin):
    __tablename__ = "provider_services"
    __table_args__ = (
        db.UniqueConstraint("provider_user_id", "service_id", name="uq_provider_service"),
        db.Index("idx_ps_active", "is_active"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    provider_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_ps_user"), nullable=False)
    service_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("services.id", ondelete="CASCADE", name="fk_ps_service"), nullable=False)
    title = db.Column(db.String(180))
    description = db.Column(db.Text)
    price_from = db.Column(db.Numeric(10, 2))
    price_to = db.Column(db.Numeric(10, 2))
    is_active = db.Column(TINYINT, nullable=False, server_default="1")


class PortfolioImage(db.Model, TimestampMixin):
    __tablename__ = "portfolio_images"
    __table_args__ = (
        db.Index("idx_portfolio_user", "user_id", "created_at"),
        db.Index("idx_portfolio_user_created_id", "user_id", "created_at", "id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_portfolio_user"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))


class ServiceRequest(db.Model, TimestampMixin):
    __tablename__ = "service_requests"
    __table_args__ = (
        db.Index("idx_sr_status", "status"),
        db.Index("idx_sr_provider", "provider_id", "status"),
        db.Index("idx_sr_customer", "customer_id", "status"),
        db.Index("idx_sr_category", "category_id", "status"),
        db.Index("idx_sr_type_status_service", "request_type", "status", "service_id"),
        db.Index("idx_sr_business", "business_id", "status"),
        db.Index("idx_sr_provider_created", "provider_id", "created_at", "id"),
        db.Index("idx_sr_business_created", "business_id", "created_at", "id"),
        db.Index("idx_sr_customer_created", "customer_id", "created_at", "id"),
        db.Index("idx_sr_requirement_feed", "request_type", "status", "created_at", "id", "service_id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    customer_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_sr_customer"), nullable=False)
    provider_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_sr_provider"))
    business_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_sr_business"))
    category_id = db.Column(INT_UNSIGNED, db.ForeignKey("categories.id", name="fk_sr_category"), nullable=False)
    service_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("services.id", ondelete="SET NULL", name="fk_sr_service"))
    request_type = db.Column(enum_type("request_type", "direct", "requirement"), nullable=False, server_default="direct")
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location_text = db.Column(db.String(255), nullable=False)
    preferred_date = db.Column(db.Date)
    preferred_time = db.Column(db.Time)
    budget_min = db.Column(db.Numeric(10, 2))
    budget_max = db.Column(db.Numeric(10, 2))
    additional_notes = db.Column(db.Text)
    status = db.Column(enum_type("request_status", "pending", "accepted", "rejected", "in_progress", "completed", "cancelled"), nullable=False, server_default="pending")


class RequestStatusHistory(db.Model):
    __tablename__ = "request_status_history"
    __table_args__ = (db.Index("idx_rsh_request", "request_id", "created_at"),)

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    request_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("service_requests.id", ondelete="CASCADE", name="fk_rsh_request"), nullable=False)
    status = db.Column(enum_type("request_history_status", "pending", "accepted", "rejected", "in_progress", "completed", "cancelled"), nullable=False)
    changed_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_rsh_user"), nullable=False)
    note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class Review(db.Model, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_rating"),
        db.Index("idx_reviews_target", "target_user_id", "status"),
        db.Index("idx_reviews_customer_created", "customer_id", "created_at", "id"),
        db.Index("idx_reviews_target_created", "target_user_id", "status", "created_at", "id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    request_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("service_requests.id", ondelete="CASCADE", name="fk_review_request"), nullable=False, unique=True)
    customer_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_review_customer"), nullable=False)
    target_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_review_target"), nullable=False)
    rating = db.Column(TINYINT_UNSIGNED, nullable=False)
    comment = db.Column(db.Text)
    status = db.Column(enum_type("review_status", "published", "hidden", "removed"), nullable=False, server_default="published")


class Favorite(db.Model):
    __tablename__ = "favorites"
    __table_args__ = (
        db.UniqueConstraint("customer_id", "target_user_id", name="uq_favorite"),
        db.Index("idx_favorites_customer_created", "customer_id", "created_at", "id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    customer_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_fav_customer"), nullable=False)
    target_user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_fav_target"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (db.Index("idx_notifications_user", "user_id", "is_read", "created_at"),)

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_notification_user"), nullable=False)
    type = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(TINYINT, nullable=False, server_default="0")
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class Report(db.Model, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = (
        db.Index("idx_reports_status", "status"),
        db.Index("idx_reports_created", "created_at", "id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    reporter_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_reporter"), nullable=False)
    target_type = db.Column(enum_type("report_target_type", "provider", "business", "review"), nullable=False)
    target_id = db.Column(BIGINT_UNSIGNED, nullable=False)
    reason = db.Column(enum_type("report_reason", "fake_profile", "wrong_information", "spam", "fraud_concern", "inappropriate_content", "other"), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(enum_type("report_status", "open", "investigating", "resolved", "dismissed"), nullable=False, server_default="open")
    resolved_by = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_report_admin"))
    resolution_note = db.Column(db.String(500))
