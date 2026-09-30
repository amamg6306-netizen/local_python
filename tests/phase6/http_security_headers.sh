#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${PHASE6_BASE_URL:-}" ]]; then
  echo 'SKIP: set PHASE6_BASE_URL=https://host/base/ to execute real HTTP security-header checks.'
  exit 0
fi
[[ "$PHASE6_BASE_URL" == https://* ]] || { echo 'FAIL: PHASE6_BASE_URL must use https://' >&2; exit 1; }
headers="$(curl -fsSI --max-time 15 "$PHASE6_BASE_URL")"
for h in 'strict-transport-security:' 'content-security-policy:' 'x-content-type-options: nosniff' 'x-frame-options: deny' 'referrer-policy:'; do
  grep -qi "^${h}" <<<"$headers" || { echo "FAIL: missing $h" >&2; exit 1; }
done
echo 'PASS: HTTPS response includes required Phase 6 browser security headers.'
