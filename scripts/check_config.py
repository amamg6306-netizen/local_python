from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import production_config_errors, runtime_settings


def main() -> int:
    runtime = runtime_settings()
    print(f"APP_ENV={runtime.app_env}")
    if not runtime.production:
        print("Configuration check: development/non-production mode")
        return 0
    errors = production_config_errors()
    if errors:
        print("Configuration check: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Configuration check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
