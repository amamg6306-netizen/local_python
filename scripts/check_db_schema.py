from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import connect, connection_settings


MANIFEST = ROOT / "database" / "schema_manifest.json"


def main() -> int:
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["tables"]
    settings = connection_settings()
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema=%s AND table_type='BASE TABLE'",
                (settings.database,),
            )
            actual_tables = {row["TABLE_NAME"] for row in cursor.fetchall()}
            cursor.execute(
                "SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.columns WHERE table_schema=%s",
                (settings.database,),
            )
            actual_columns: dict[str, set[str]] = {}
            for row in cursor.fetchall():
                actual_columns.setdefault(row["TABLE_NAME"], set()).add(row["COLUMN_NAME"])
            cursor.execute(
                "SELECT TABLE_NAME,INDEX_NAME FROM information_schema.statistics WHERE table_schema=%s",
                (settings.database,),
            )
            actual_indexes: dict[str, set[str]] = {}
            for row in cursor.fetchall():
                actual_indexes.setdefault(row["TABLE_NAME"], set()).add(row["INDEX_NAME"])
            cursor.execute("SELECT 1 AS ok")
            ping = cursor.fetchone()["ok"]

    missing_tables = sorted(set(expected) - actual_tables)
    missing_columns: list[str] = []
    missing_indexes: list[str] = []
    for table, spec in expected.items():
        if table not in actual_tables:
            continue
        for column in spec["columns"]:
            if column not in actual_columns.get(table, set()):
                missing_columns.append(f"{table}.{column}")
        for index in spec["indexes"] + spec["unique_constraints"]:
            if index not in actual_indexes.get(table, set()):
                missing_indexes.append(f"{table}.{index}")

    print(
        f"Database: {settings.database}; connectivity={ping}; "
        f"expected_tables={len(expected)}; actual_tables={len(actual_tables)}"
    )
    if missing_tables:
        print("Missing tables:", ", ".join(missing_tables))
    if missing_columns:
        print("Missing columns:", ", ".join(missing_columns))
    if missing_indexes:
        print("Missing indexes/unique keys:", ", ".join(missing_indexes))
    return 1 if (missing_tables or missing_columns or missing_indexes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
