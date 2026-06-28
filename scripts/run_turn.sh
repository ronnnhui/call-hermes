#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/server/.env}"

if ! command -v turnserver >/dev/null 2>&1; then
  echo "turnserver is not installed. Install coturn first, then rerun this script."
  exit 1
fi

read_env() {
  local key="$1"
  if [ ! -f "${ENV_FILE}" ]; then
    return 0
  fi
  grep -E "^${key}=" "${ENV_FILE}" | tail -1 | cut -d= -f2-
}

TURN_USERNAME="$(read_env ICE_TURN_USERNAME)"
TURN_CREDENTIAL="$(read_env ICE_TURN_CREDENTIAL)"
PUBLIC_BASE_URL="$(read_env PUBLIC_BASE_URL)"

if [ -z "${TURN_USERNAME}" ] || [ -z "${TURN_CREDENTIAL}" ]; then
  echo "Missing TURN env. Set ICE_TURN_USERNAME and ICE_TURN_CREDENTIAL in ${ENV_FILE}"
  exit 1
fi

REALM="${TURN_REALM:-${PUBLIC_BASE_URL#https://}}"
REALM="${REALM#http://}"
REALM="${REALM%%:*}"
REALM="${REALM:-localhost}"
LISTENING_PORT="${TURN_PORT:-10004}"

TMP_CONF="$(mktemp)"
trap 'rm -f "${TMP_CONF}"' EXIT

cat > "${TMP_CONF}" <<EOF
listening-port=${LISTENING_PORT}
fingerprint
lt-cred-mech
realm=${REALM}
server-name=${REALM}
user=${TURN_USERNAME}:${TURN_CREDENTIAL}
total-quota=100
bps-capacity=0
stale-nonce=600
no-loopback-peers
no-multicast-peers
mobility
EOF

echo "Starting coturn realm=${REALM} port=${LISTENING_PORT} user=${TURN_USERNAME}"
exec turnserver -c "${TMP_CONF}"
