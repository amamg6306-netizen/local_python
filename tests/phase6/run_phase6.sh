#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
echo '== PHP syntax lint =='
count=0
while IFS= read -r -d '' f; do php -l "$f" >/dev/null; count=$((count+1)); done < <(find . -type f -name '*.php' -print0)
echo "PASS: ${count} PHP files linted"
echo '== Phase 6 PHP helper checks =='
php tests/phase6/php_security_helpers.php
echo '== Phase 6 static production hardening =='
python3 tests/phase6/static_hardening_phase6.py
echo '== Secret scan =='
python3 tools/secret_scan.py
echo '== Dependency/external-resource inventory =='
python3 tools/dependency_inventory.py
echo '== Shell syntax =='
bash -n tools/backup_database.sh tools/restore_database.sh tests/phase6/http_security_headers.sh
echo 'PASS: deployment shell scripts parse'
echo '== HTTP header check =='
tests/phase6/http_security_headers.sh
echo '== Phase 5 and earlier regressions =='
tests/phase5/run_phase5.sh
echo '== Release gate fail-safe expectation for packaged artifact =='
set +e
php tools/release_gate.php --json >/tmp/localconnect-release-gate.json 2>/tmp/localconnect-release-gate.err
rc=$?
set -e
if [[ $rc -ne 2 ]]; then cat /tmp/localconnect-release-gate.json /tmp/localconnect-release-gate.err >&2 || true; echo "FAIL: packaged release gate should be NOT READY (exit 2), got $rc" >&2; exit 1; fi
grep -q 'NOT_READY_FOR_LIVE_PAYMENTS' /tmp/localconnect-release-gate.json || { cat /tmp/localconnect-release-gate.json >&2; echo 'FAIL: release gate did not report safe NOT READY status' >&2; exit 1; }
echo 'PASS: packaged artifact fails closed for live payments until external evidence/configuration exists.'
