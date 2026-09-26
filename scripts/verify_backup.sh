#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
TMP="${1:-diamond_verify_$(date +%Y%m%d_%H%M%S).dump}"
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" -f "$TMP"
pg_restore --list "$TMP" >/dev/null
sha256sum "$TMP" > "$TMP.sha256"
echo "Backup verified: $TMP"
echo "Checksum: $TMP.sha256"
