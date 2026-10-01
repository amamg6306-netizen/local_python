from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.settings import database_uri, env_bool, env_int, env_value


@dataclass(frozen=True)
class DatabaseConnectionSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl_enabled: bool
    connect_timeout: int
    read_timeout: int
    write_timeout: int


def connection_settings(*, migration: bool = False) -> DatabaseConnectionSettings:
    # migration is retained for CLI compatibility; PostgreSQL uses the same
    # production connection for schema bootstrap/checks.
    url = database_uri(env_value("APP_ENV", "development") == "production")
    parsed = urlsplit(url)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg"}:
        raise RuntimeError("DATABASE_URL/DB_* configuration must point to PostgreSQL.")
    if not parsed.hostname or not parsed.path.lstrip("/") or not parsed.username:
        raise RuntimeError("PostgreSQL URL must include host, database, and user.")
    return DatabaseConnectionSettings(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password or "",
        ssl_enabled=env_bool("DB_SSL", False),
        connect_timeout=env_int("DB_CONNECT_TIMEOUT", 10, minimum=1, maximum=120),
        read_timeout=env_int("DB_READ_TIMEOUT", 30, minimum=1, maximum=300),
        write_timeout=env_int("DB_WRITE_TIMEOUT", 30, minimum=1, maximum=300),
    )


def create_database_engine(*, migration: bool = False) -> Engine:
    url = database_uri(env_value("APP_ENV", "development") == "production")
    connect_args = {
        "connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10, minimum=1, maximum=120),
    }
    # psycopg accepts sslmode; Render normally handles TLS in its DATABASE_URL.
    if env_bool("DB_SSL", False):
        connect_args["sslmode"] = env_value("DB_SSLMODE", "require") or "require"
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=env_int("DB_POOL_RECYCLE", 280, minimum=30, maximum=3600),
        pool_size=env_int("DB_POOL_SIZE", 5, minimum=1, maximum=50),
        max_overflow=env_int("DB_MAX_OVERFLOW", 10, minimum=0, maximum=100),
        pool_timeout=env_int("DB_POOL_TIMEOUT", 30, minimum=1, maximum=120),
        connect_args=connect_args,
    )


def connect(*, migration: bool = False):
    """Compatibility helper returning a SQLAlchemy Connection."""
    return create_database_engine(migration=migration).connect()
