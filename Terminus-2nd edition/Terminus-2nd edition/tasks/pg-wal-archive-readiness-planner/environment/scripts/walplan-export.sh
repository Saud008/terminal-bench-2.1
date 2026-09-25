#!/usr/bin/env bash
# Export restore planner JSON from staging (alias for plan).
set -euo pipefail
exec bash "${APP_ROOT:-/app}/scripts/walplan-plan.sh" "$@"
