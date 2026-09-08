#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
FILE="${1:?usage: restore_postgres.sh backup.dump}"
echo "WARNING: restoring into the database configured by DATABASE_URL"
pg_restore --clean --if-exists --no-owner --no-acl -d "$DATABASE_URL" "$FILE"
echo "Restore complete"
