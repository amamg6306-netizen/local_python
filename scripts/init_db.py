from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import connect, connection_settings
from database.sql_runner import execute_sql_file


SCHEMA = ROOT / "database" / "schema.sql"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize an empty LocalConnect MySQL/MariaDB database safely.")
    parser.add_argument("--yes", action="store_true", help="Confirm initialization after the empty-database check.")
    args = parser.parse_args()

    settings = connection_settings(migration=True)
    with connect(migration=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema=%s AND table_type='BASE TABLE'",
                (settings.database,),
            )
            table_count = int(cursor.fetchone()["table_count"])
        if table_count:
            raise RuntimeError(
                f"Refusing fresh initialization: database {settings.database!r} already has {table_count} base table(s). "
                "Use scripts/migrate_db.py for an existing database."
            )
        if not args.yes:
            print(f"Database {settings.database!r} is empty. Re-run with --yes to apply database/schema.sql.")
            return 2
        count = execute_sql_file(connection, SCHEMA, skip_use=True)
        print(f"Initialized {settings.database!r} from {SCHEMA.name}; executed {count} SQL statement(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
