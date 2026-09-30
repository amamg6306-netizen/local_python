#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${BACKUP_DB_HOST:?Set BACKUP_DB_HOST}"
: "${BACKUP_DB_NAME:?Set BACKUP_DB_NAME}"
: "${BACKUP_DB_USER:?Set BACKUP_DB_USER}"
: "${BACKUP_DB_PASS:?Set BACKUP_DB_PASS}"
out="${1:-./localconnect-backup-$(date -u +%Y%m%dT%H%M%SZ).sql.gz}"
tmp_cnf="$(mktemp)"; tmp_sql="${out%.gz}.partial.sql"
trap 'rm -f "$tmp_cnf" "$tmp_sql"' EXIT
chmod 600 "$tmp_cnf"
cat > "$tmp_cnf" <<EOF
[client]
host=${BACKUP_DB_HOST}
port=${BACKUP_DB_PORT:-3306}
user=${BACKUP_DB_USER}
password=${BACKUP_DB_PASS}
EOF
mysqldump --defaults-extra-file="$tmp_cnf" --single-transaction --quick --hex-blob --routines --triggers "$BACKUP_DB_NAME" > "$tmp_sql"
gzip -c "$tmp_sql" > "$out"
sha256sum "$out" > "${out}.sha256"
echo "Backup written: $out"
echo "Checksum written: ${out}.sha256"
