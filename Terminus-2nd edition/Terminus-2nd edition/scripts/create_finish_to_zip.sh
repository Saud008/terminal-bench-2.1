#!/usr/bin/env bash
# CREATE Phases E(static) → F → F′ → G — one command until tasksubmit/<name>.zip
# Usage: ./scripts/create_finish_to_zip.sh <task-name> [extra args...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    python="$cmd"
    break
  fi
done

if [ -z "$python" ]; then
  echo "ERROR: python3 not found" >&2
  exit 1
fi

TASK_NAME="${1:-}"
shift || true

if [ -z "$TASK_NAME" ]; then
  echo "Usage: $(basename "$0") <task-name> [--skip-harbor --oracle 1.0 --nop 0.0 ...]" >&2
  exit 1
fi

exec "$python" "$REPO_ROOT/scripts/create_finish_to_zip.py" --task-name "$TASK_NAME" "$@"
