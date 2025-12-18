#!/usr/bin/env bash
set -euo pipefail

PORT=9002
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$DIR"

echo "Serving $DIR on http://localhost:${PORT}/slides-react.html"

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m http.server "$PORT"
elif command -v python >/dev/null 2>&1; then
  exec python -m http.server "$PORT"
else
  echo "Error: python3/python not found in PATH" >&2
  exit 1
fi
