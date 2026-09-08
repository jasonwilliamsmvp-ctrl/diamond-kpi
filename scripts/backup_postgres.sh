#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
OUT="${1:-diamond_backup_$(date +%Y%m%d_%H%M%S).dump}"
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" -f "$OUT"
echo "Backup created: $OUT"
