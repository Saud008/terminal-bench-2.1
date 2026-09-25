#!/usr/bin/env bash
# TRIVIAL/EASY steps 8–14 — automated pipeline (LOCKED entrypoint).
# Usage: ./scripts/trivial_easy_auto_finish.sh <task-name> [extra args for .py]
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK_NAME="${1:?usage: ./scripts/trivial_easy_auto_finish.sh <task-name>}"
shift || true
python3="$(command -v python3 || true)"
if [ -z "$python3" ]; then
  python3="$(command -v python || true)"
fi
exec "$python3" "$REPO_ROOT/scripts/trivial_easy_auto_finish.py" --task-name "$TASK_NAME" "$@"
