#!/usr/bin/env bash
# Install ContextBridge skills into host discovery directories (.agents / .claude / .cursor).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 "$ROOT/scripts/install_skills.py" "$@"
