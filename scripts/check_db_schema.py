from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: F401
from database.connection import create_database_engine, connection_settings

MANIFEST = ROOT / "database" / "schema_manifest.json"


def main() -> int:
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["tables"]
    settings = connection_settings()
    engine = create_database_engine()
    inspector = inspect(engine)

    actual_tables = set(inspector.get_table_names())
    actual_columns: dict[str, set[str]] = {}
    actual_indexes: dict[str, set[str]] = {}
    actual_unique: dict[str, set[str]] = {}
    for table in actual_tables:
        actual_columns[table] = {column["name"] for column in inspector.get_columns(table)}
        actual_indexes[table] = {index["name"] for index in inspector.get_indexes(table) if index.get("name")}
        actual_unique[table] = {constraint["name"] for constraint in inspector.get_unique_constraints(table) if constraint.get("name")}
        # PostgreSQL exposes primary-key names separately; manifest does not
        # require them, so they are intentionally ignored here.

    with engine.connect() as connection:
        ping = connection.execute(text("SELECT 1")).scalar_one()

    missing_tables = sorted(set(expected) - actual_tables)
    missing_columns: list[str] = []
    missing_indexes: list[str] = []
    for table, spec in expected.items():
        if table not in actual_tables:
            continue
        for column in spec["columns"]:
            if column not in actual_columns.get(table, set()):
                missing_columns.append(f"{table}.{column}")
        names = actual_indexes.get(table, set()) | actual_unique.get(table, set())
        for index in spec["indexes"] + spec["unique_constraints"]:
            if index not in names:
                missing_indexes.append(f"{table}.{index}")

    print(
        f"PostgreSQL database: {settings.database}; connectivity={ping}; "
        f"expected_tables={len(expected)}; actual_tables={len(actual_tables)}"
    )
    if missing_tables:
        print("Missing tables:", ", ".join(missing_tables))
    if missing_columns:
        print("Missing columns:", ", ".join(missing_columns))
    if missing_indexes:
        print("Missing indexes/unique keys:", ", ".join(missing_indexes))

    engine.dispose()
    return 1 if (missing_tables or missing_columns or missing_indexes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
