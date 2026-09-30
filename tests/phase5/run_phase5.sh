#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo '== PHP syntax lint =='
count=0
while IFS= read -r -d '' f; do php -l "$f" >/dev/null; count=$((count+1)); done < <(find . -type f -name '*.php' -print0)
echo "PASS: ${count} PHP files linted"
echo '== Phase 5 static performance/reliability controls =='
python3 tests/phase5/static_performance_phase5.py
echo '== Phase 5 memory buffering proxy =='
python3 tests/phase5/memory_proxy_benchmark.py
echo '== Phase 4 payment regressions =='
php tests/phase4/php_billing_helpers.php
python3 tests/phase4/static_checkout_security.py
echo '== Phase 3 regressions =='
php tests/phase3/php_payment_helpers.php
python3 tests/phase3/static_payment_methods.py
echo '== Phase 2 security regressions =='
php tests/phase2/php_security_helpers.php
python3 tests/phase2/static_security_phase2.py
echo '== Baseline security scanner =='
python3 tests/phase1/static_security_baseline.py
