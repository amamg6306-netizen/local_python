#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${RESTORE_CONFIRM:?Set RESTORE_CONFIRM=YES after verifying the target is a restore/rehearsal database}"
[[ "$RESTORE_CONFIRM" == "YES" ]] || { echo 'RESTORE_CONFIRM must be YES' >&2; exit 2; }
: "${RESTORE_DB_HOST:?Set RESTORE_DB_HOST}"
: "${RESTORE_DB_NAME:?Set RESTORE_DB_NAME}"
: "${RESTORE_DB_USER:?Set RESTORE_DB_USER}"
: "${RESTORE_DB_PASS:?Set RESTORE_DB_PASS}"
file="${1:?Usage: restore_database.sh backup.sql.gz}"
[[ -f "$file" ]] || { echo 'Backup file not found' >&2; exit 2; }
if [[ -f "${file}.sha256" ]]; then sha256sum -c "${file}.sha256"; fi
tmp_cnf="$(mktemp)"; trap 'rm -f "$tmp_cnf"' EXIT; chmod 600 "$tmp_cnf"
cat > "$tmp_cnf" <<EOF
[client]
host=${RESTORE_DB_HOST}
port=${RESTORE_DB_PORT:-3306}
user=${RESTORE_DB_USER}
password=${RESTORE_DB_PASS}
EOF
gzip -dc "$file" | mysql --defaults-extra-file="$tmp_cnf" "$RESTORE_DB_NAME"
echo "Restore completed into explicitly selected database: $RESTORE_DB_NAME"
