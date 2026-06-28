#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://127.0.0.1:10005}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

python3 - "$BASE_URL" <<'PY'
import json
import ssl
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")
ctx = ssl._create_unverified_context()
data = urllib.request.urlopen(f"{base_url}/health", timeout=10, context=ctx).read()
health = json.loads(data)
config = health.get("config", {})
checks = config.get("checks", {})

print(f"health ok: {health.get('ok')}")
print(f"config ok: {config.get('ok')}")
for name, check in checks.items():
    status = "ok" if check.get("ok") else "WARN"
    print(f"{status:4} {name}: {check.get('detail')}")

errors = config.get("errors") or []
if errors:
    print("config errors:", ", ".join(errors))
    raise SystemExit(1)
PY
