from __future__ import annotations

from extensions import db
from models.base import BIGINT_UNSIGNED, INT_UNSIGNED, enum_type, now_default


class SchemaMigration(db.Model):
    __tablename__ = "schema_migrations"

    version = db.Column(db.String(80), primary_key=True)
    applied_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    checksum_sha256 = db.Column(db.String(64))


class AuthToken(db.Model):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        db.UniqueConstraint("selector", name="uq_auth_token_selector"),
        db.Index("idx_auth_token_user", "user_id", "purpose", "used_at", "expires_at"),
        db.Index("idx_auth_token_expiry", "purpose", "used_at", "expires_at"),
    )

    id = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_auth_token_user"), nullable=False)
    purpose = db.Column(enum_type("auth_token_purpose", "password_reset", "email_verify"), nullable=False)
    selector = db.Column(db.String(16), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    requested_ip_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())


class AuthRateLimit(db.Model):
    __tablename__ = "auth_rate_limits"
    __table_args__ = (db.Index("idx_auth_rate_blocked", "blocked_until"),)

    bucket_hash = db.Column(db.String(64), primary_key=True)
    attempts = db.Column(INT_UNSIGNED, nullable=False, server_default="0")
    window_started_at = db.Column(db.DateTime, nullable=False)
    blocked_until = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), server_onupdate=now_default())


class AdminMfa(db.Model):
    __tablename__ = "admin_mfa"

    user_id = db.Column(BIGINT_UNSIGNED, db.ForeignKey("users.id", ondelete="CASCADE", name="fk_admin_mfa_user"), primary_key=True)
    secret_ciphertext = db.Column(db.Text, nullable=False)
    secret_nonce = db.Column(db.String(128), nullable=False)
    encryption_alg = db.Column(db.String(40), nullable=False)
    enabled_at = db.Column(db.DateTime, nullable=False)
    last_used_step = db.Column(db.BigInteger)
    last_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=now_default(), server_onupdate=now_default())
