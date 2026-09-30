#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo '== PHP syntax lint =='
count=0
while IFS= read -r -d '' f; do php -l "$f" >/dev/null; count=$((count+1)); done < <(find . -type f -name '*.php' -print0)
echo "PASS: ${count} PHP files linted"
echo '== Phase 3 helper tests =='
php tests/phase3/php_payment_helpers.php
echo '== Phase 3 static controls =='
python3 tests/phase3/static_payment_methods.py
echo '== Phase 2 security regression =='
php tests/phase2/php_security_helpers.php
python3 tests/phase2/static_security_phase2.py
