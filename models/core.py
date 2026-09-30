from __future__ import annotations

from extensions import db
from models.base import (
    BIGINT_UNSIGNED,
    INT_UNSIGNED,
    TINYINT,
    TINYINT_UNSIGNED,
    TimestampMixin,
    enum_type,
    now_default,
)


class User(db.Model, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        db.Index("idx_users_role_status", "role", "status"),
        db.Index("idx_users_location", "city", "state", "area"),
        db.Index("idx_users_name", "name"),
        db.Index("idx_users_role_status_id", "role", "status", "id"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(190), nullable=False, unique=True)
    phone = db.Column(db.String(25))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(enum_type("user_role", "customer", "provider", "business", "admin"), nullable=False, server_default="customer")
    status = db.Column(enum_type("user_status", "active", "blocked", "pending"), nullable=False, server_default="active")
    profile_image = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    area = db.Column(db.String(150))
    pincode = db.Column(db.String(12))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    last_login_at = db.Column(db.DateTime)
    email_verified_at = db.Column(db.DateTime)
    session_version = db.Column(INT_UNSIGNED, nullable=False, server_default="1")


class Location(db.Model, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (db.Index("idx_locations_city", "city", "state", "area"),)

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_locations_user"), nullable=False)
    label = db.Column(db.String(80), server_default="Primary")
    address_line = db.Column(db.String(255))
    area = db.Column(db.String(150))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(12))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    is_default = db.Column(TINYINT, nullable=False, server_default="0")


class Category(db.Model, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (db.Index("idx_categories_active", "is_active"),)

    id = db.Column(INT_UNSIGNED, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(140), nullable=False, unique=True)
    icon = db.Column(db.String(80))
    description = db.Column(db.String(255))
    is_active = db.Column(TINYINT, nullable=False, server_default="1")


class PlatformActivity(db.Model):
    __tablename__ = "platform_activity"
    __table_args__ = (
        db.Index("idx_activity_created", "created_at"),
        db.Index("idx_activity_action", "action"),
        db.Index("idx_activity_actor_created", "actor_id", "created_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    actor_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="SET NULL", name="fk_activity_actor"))
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(60))
    target_id = db.Column(BIGINT_UNSIGNED)
    details = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
