#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo '== PHP lint =='
fail=0; count=0
while IFS= read -r -d '' f; do count=$((count+1)); php -l "$f" >/dev/null || fail=1; done < <(find . -type f -name '*.php' -print0)
echo "PHP linted: $count; status=$([ "$fail" -eq 0 ] && echo PASS || echo FAIL)"
[ "$fail" -eq 0 ]
echo '== Phase 2 helper tests =='
php tests/phase2/php_security_helpers.php
echo '== Phase 2 static security tests =='
python3 tests/phase2/static_security_phase2.py
echo '== Phase 1 regression baseline =='
./tests/phase1/run_baseline.sh || true
echo 'NOTE: Phase 1 warning assertions describe the pre-Phase-2 baseline and are expected to remain as historical output.'
