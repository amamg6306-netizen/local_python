from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_db_schema import main as check_schema_main


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check/bootstrap the LocalConnect PostgreSQL schema."
    )
    parser.add_argument("--apply", action="store_true", help="Create missing PostgreSQL schema objects and reference data.")
    parser.add_argument("--preflight", action="store_true", help="Retained for CLI compatibility; PostgreSQL bootstrap is metadata-driven.")
    args = parser.parse_args()

    if not args.apply:
        print("PostgreSQL migration status: run scripts/check_db_schema.py for the current schema.")
        return check_schema_main()

    # init_db.py owns the actual bootstrap logic; this command is retained as
    # the familiar migration entry point for existing operational runbooks.
    import subprocess
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "init_db.py"), "--yes"], check=False)
    if completed.returncode:
        return completed.returncode
    return check_schema_main()


if __name__ == "__main__":
    raise SystemExit(main())
