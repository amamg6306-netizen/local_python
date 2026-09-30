from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import connect, connection_settings
from database.sql_runner import execute_sql_file, file_checksum


MIGRATION_DIR = ROOT / "database" / "production"
FORWARD_RE = re.compile(r"^(\d{8}_\d{3}_[a-z0-9_]+)\.sql$")


def forward_migrations() -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for path in sorted(MIGRATION_DIR.glob("*.sql")):
        if path.stem.endswith(("_preflight", "_rollback")):
            continue
        match = FORWARD_RE.match(path.name)
        if match:
            result.append((match.group(1), path))
    return result


def ensure_tracking_table(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(80) PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                checksum_sha256 CHAR(64) NULL
            ) ENGINE=InnoDB
            """
        )


def applied_migrations(connection) -> dict[str, str | None]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version, checksum_sha256 FROM schema_migrations")
        return {row["version"]: row["checksum_sha256"] for row in cursor.fetchall()}


def record_checksum(connection, version: str, checksum: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO schema_migrations(version, checksum_sha256)
            VALUES(%s, %s)
            ON DUPLICATE KEY UPDATE checksum_sha256=VALUES(checksum_sha256)
            """,
            (version, checksum),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply LocalConnect forward-only production database migrations.")
    parser.add_argument("--apply", action="store_true", help="Apply pending migrations. Without this flag, only status is shown.")
    parser.add_argument("--preflight", action="store_true", help="Run matching read-only preflight SQL before each pending migration.")
    args = parser.parse_args()

    settings = connection_settings(migration=True)
    with connect(migration=True) as connection:
        ensure_tracking_table(connection)
        applied = applied_migrations(connection)
        pending: list[tuple[str, Path, str]] = []

        for version, path in forward_migrations():
            checksum = file_checksum(path)
            if version in applied:
                recorded = applied[version]
                if recorded and recorded != checksum:
                    raise RuntimeError(
                        f"Checksum mismatch for already-applied migration {version}; refusing to continue."
                    )
                print(f"APPLIED {version}")
            else:
                pending.append((version, path, checksum))
                print(f"PENDING {version}")

        if not pending:
            print("Database migration status: current.")
            return 0
        if not args.apply:
            print(f"{len(pending)} migration(s) pending for database {settings.database!r}. Re-run with --apply after backup/preflight review.")
            return 2

        for version, path, checksum in pending:
            if args.preflight:
                candidates = [
                    path.with_name(path.stem + "_preflight.sql"),
                    path.with_name("_".join(path.stem.split("_")[:2]) + "_preflight.sql"),
                ]
                preflight = next((candidate for candidate in candidates if candidate.exists()), None)
                if preflight is not None:
                    print(f"PREFLIGHT {preflight.name}")
                    execute_sql_file(connection, preflight, skip_use=True, echo_results=True)
            print(f"APPLY {path.name}")
            execute_sql_file(connection, path, skip_use=True)
            record_checksum(connection, version, checksum)

        print(f"Applied {len(pending)} migration(s) to database {settings.database!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
