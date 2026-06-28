#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${PID_FILE:-${ROOT_DIR}/server/voice-bridge-https.pid}"

if [ ! -f "${PID_FILE}" ]; then
  echo "No PID file found: ${PID_FILE}"
  exit 0
fi

PID="$(cat "${PID_FILE}")"
if kill -0 "${PID}" 2>/dev/null; then
  kill "${PID}"
  echo "Stopped HTTPS voice bridge pid ${PID}"
elif sudo -n kill -0 "${PID}" 2>/dev/null; then
  sudo -n kill "${PID}"
  echo "Stopped HTTPS voice bridge pid ${PID}"
else
  echo "Process ${PID} is not running"
fi
rm -f "${PID_FILE}"
