#!/usr/bin/env bash
# Backs up the production SQLite database out of the running `backend` container.
# Uses sqlite3's Connection.backup() (via Python) instead of a raw file copy, so the
# backup stays consistent even if the app is writing to the database at the same time.
#
# Usage (run from the directory containing docker-compose.yml):
#   ./scripts/backup_db.sh [output-directory]
#
# Defaults to ./backups in the current directory. Keeps the last 14 backups and
# deletes older ones.

set -euo pipefail

OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REMOTE_TMP="/data/billing_report_backup_${TIMESTAMP}.db"
LOCAL_FILE="${OUT_DIR}/billing_report_${TIMESTAMP}.db"

echo "Creating consistent snapshot inside the container..."
docker compose exec -T backend python -c "
import sqlite3
src = sqlite3.connect('/data/billing_report.db')
dst = sqlite3.connect('${REMOTE_TMP}')
src.backup(dst)
src.close()
dst.close()
"

echo "Copying snapshot to ${LOCAL_FILE}..."
docker compose cp "backend:${REMOTE_TMP}" "$LOCAL_FILE"

echo "Cleaning up temporary snapshot inside the container..."
docker compose exec -T backend rm -f "$REMOTE_TMP"

echo "Backup saved: ${LOCAL_FILE}"

echo "Pruning backups older than the last 14..."
ls -1t "${OUT_DIR}"/billing_report_*.db 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "Done."
