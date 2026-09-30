#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCROOT="$(dirname "$ROOT")"
PORT="${LC_TEST_PORT:-18081}"
LOG="${TMPDIR:-/tmp}/localconnect_phase1_http.log"
HEADERS="${TMPDIR:-/tmp}/localconnect_phase1_headers.txt"
BODY="${TMPDIR:-/tmp}/localconnect_phase1_body.html"
php -S "127.0.0.1:${PORT}" -t "$DOCROOT" >"$LOG" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
sleep 0.7
curl -fsS -D "$HEADERS" -o "$BODY" "http://127.0.0.1:${PORT}/localconnect/about.php"
grep -qi '^HTTP/.* 200' "$HEADERS"
grep -qi '^X-Content-Type-Options: nosniff' "$HEADERS"
grep -qi '^X-Frame-Options: SAMEORIGIN' "$HEADERS"
grep -qi '^Referrer-Policy: strict-origin-when-cross-origin' "$HEADERS"
grep -q '<title>About LocalConnect</title>' "$BODY"
echo 'PASS: public-page HTTP/header smoke (about.php)'
