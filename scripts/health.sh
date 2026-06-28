#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://127.0.0.1:10005}"
curl -k -fsS "${BASE_URL}/health"
