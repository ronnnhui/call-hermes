#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://127.0.0.1:10005}"
SHARED_SECRET="${APP_SHARED_SECRET:-dev-shared-secret-change-me-32-bytes}"

curl -fsS \
  -k \
  -H "Content-Type: application/json" \
  -d "{\"shared_secret\":\"${SHARED_SECRET}\",\"device_name\":\"shell\"}" \
  "${BASE_URL}/auth/session"
