#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/server/.env}"

read_env() {
  local key="$1"
  if [ ! -f "${ENV_FILE}" ]; then
    return 0
  fi
  grep -E "^${key}=" "${ENV_FILE}" | tail -1 | cut -d= -f2-
}

TURN_URLS="$(read_env ICE_TURN_URLS)"
TURN_USERNAME="$(read_env ICE_TURN_USERNAME)"
TURN_CREDENTIAL="$(read_env ICE_TURN_CREDENTIAL)"

if [ -z "${TURN_URLS}" ] && [ -z "${TURN_USERNAME}" ] && [ -z "${TURN_CREDENTIAL}" ]; then
  echo "TURN is not configured in ${ENV_FILE}"
  exit 1
fi

if [ -z "${TURN_URLS}" ] || [ -z "${TURN_USERNAME}" ] || [ -z "${TURN_CREDENTIAL}" ]; then
  echo "TURN config is incomplete in ${ENV_FILE}"
  echo "Required: ICE_TURN_URLS, ICE_TURN_USERNAME, ICE_TURN_CREDENTIAL"
  exit 1
fi

FIRST_URL="${TURN_URLS%%,*}"
URL_NO_SCHEME="${FIRST_URL#turn:}"
URL_NO_SCHEME="${URL_NO_SCHEME#turns:}"
HOST_PORT="${URL_NO_SCHEME%%\?*}"
HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"

echo "TURN config present"
echo "First TURN server: ${HOST}:${PORT}"
echo "Username: ${TURN_USERNAME}"
echo "Credential: configured"

if command -v nc >/dev/null 2>&1; then
  if nc -vz -w 3 "${HOST}" "${PORT}" >/dev/null 2>&1; then
    echo "TCP reachability: ok"
  else
    echo "TCP reachability: failed or UDP-only TURN server"
  fi
else
  echo "TCP reachability: skipped, nc not installed"
fi
