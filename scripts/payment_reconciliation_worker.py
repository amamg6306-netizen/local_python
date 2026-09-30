from __future__ import annotations

import argparse
import json

from app import create_app
from services.billing_service import run_reconciliation_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Process bounded LocalConnect payment reconciliation jobs.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum jobs to claim in this run (1-100).")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        stats = run_reconciliation_batch(args.limit)
    print(json.dumps(stats, sort_keys=True))
    return 0 if stats.get("dead", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
