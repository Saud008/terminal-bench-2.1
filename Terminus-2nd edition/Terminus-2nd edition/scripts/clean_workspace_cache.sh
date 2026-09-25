#!/usr/bin/env bash
# Remove regenerable caches only — never touches tasks/, tasksubmit/, archive/, engines/.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "Cleaning Terminus workspace caches (tasks/ and zips untouched)..."

# Python bytecode
find scripts .cursor/hooks -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# Repo-root tool caches
rm -rf .ruff_cache .pytest_cache .mypy_cache 2>/dev/null || true

# jobs-local: reports regenerate; drop heavy index + old harbor job dirs
JOBS="$REPO_ROOT/jobs-local"
if [[ -d "$JOBS" ]]; then
  rm -f "$JOBS/anti-spam-index.json" 2>/dev/null || true
  rm -f "$JOBS/anti-spam-hook-state.json" 2>/dev/null || true
  rm -f "$JOBS/harbor-llmaj-last.json" 2>/dev/null || true
  find "$JOBS" -mindepth 1 -maxdepth 1 -type d ! -name '.' -exec rm -rf {} + 2>/dev/null || true
  touch "$JOBS/.gitkeep"
fi

# Optional: drop unused legacy Python policy stubs (hooks use terminus_rules_engine.py + ENGINE_*.mdc)
if [[ -d scripts/terminus_rules ]]; then
  rm -rf scripts/terminus_rules
  echo "Removed unused scripts/terminus_rules/"
fi

echo "Done. Re-run: python3 scripts/terminus_engine_healthcheck.py"
