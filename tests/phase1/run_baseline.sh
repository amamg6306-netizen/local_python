#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
status=0

echo '== PHP syntax lint =='
while IFS= read -r -d '' file; do
  php -l "$file" >/dev/null || status=1
done < <(find . -type f -name '*.php' -print0)
if [ "$status" -eq 0 ]; then echo 'PASS: PHP syntax lint'; fi

echo '== PHP helper smoke =='
php tests/phase1/php_helper_smoke.php || status=1

echo '== Static security baseline =='
python3 tests/phase1/static_security_baseline.py || status=1

echo '== HTTP/header smoke == '
if command -v curl >/dev/null 2>&1; then
  tests/phase1/http_header_smoke.sh || status=1
else
  echo 'SKIP: curl not installed'
fi

echo '== Runtime dependency check =='
php -r 'echo "PHP ".PHP_VERSION."\n"; echo "PDO drivers: ".implode(",",PDO::getAvailableDrivers())."\n";'
if php -r 'exit(in_array("mysql", PDO::getAvailableDrivers(), true) ? 0 : 1);'; then
  echo 'INFO: pdo_mysql available; DB/browser integration still requires configured MySQL and test DB.'
else
  echo 'SKIP: pdo_mysql is unavailable in this audit container, so DB-backed/browser tests are not claimed.'
fi

exit "$status"
