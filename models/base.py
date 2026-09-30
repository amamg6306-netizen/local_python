from __future__ import annotations

from sqlalchemy.dialects import mysql

from extensions import db


BIGINT_UNSIGNED = db.BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql")
INT_UNSIGNED = db.Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql")
SMALLINT_UNSIGNED = db.SmallInteger().with_variant(mysql.SMALLINT(unsigned=True), "mysql")
TINYINT_UNSIGNED = db.SmallInteger().with_variant(mysql.TINYINT(unsigned=True), "mysql")
TINYINT = db.SmallInteger().with_variant(mysql.TINYINT(), "mysql")


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
        server_onupdate=now_default(),
    )
