#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export TERM="${TERM:-xterm}"
echo '== PHP syntax lint =='
count=0
while IFS= read -r -d '' f; do php -l "$f" >/dev/null; count=$((count+1)); done < <(find . -type f -name '*.php' -print0)
echo "PASS: ${count} PHP files linted"
echo '== Phase 4 billing helper tests =='
php tests/phase4/php_billing_helpers.php
echo '== Phase 4 checkout/webhook static controls =='
python3 tests/phase4/static_checkout_security.py
echo '== Phase 3 regressions =='
php tests/phase3/php_payment_helpers.php
python3 tests/phase3/static_payment_methods.py
echo '== Phase 2 security regressions =='
php tests/phase2/php_security_helpers.php
python3 tests/phase2/static_security_phase2.py
echo '== Baseline security scanner =='
python3 tests/phase1/static_security_baseline.py
