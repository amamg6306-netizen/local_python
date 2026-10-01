from __future__ import annotations

from extensions import db

# Keep these aliases backend-neutral.  The application only needs integer
# identifiers/counters; UNSIGNED/TINYINT are MySQL-specific concepts and are
# intentionally not emitted for PostgreSQL.
BIGINT_UNSIGNED = db.BigInteger()
INT_UNSIGNED = db.Integer()
SMALLINT_UNSIGNED = db.SmallInteger()
TINYINT_UNSIGNED = db.SmallInteger()
TINYINT = db.SmallInteger()


def enum_type(name: str, *values: str):
    return db.Enum(*values, name=name, native_enum=True, create_constraint=True)


def now_default():
    return db.func.current_timestamp()


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, server_default=now_default())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=now_default(),
        onupdate=now_default(),
    )
