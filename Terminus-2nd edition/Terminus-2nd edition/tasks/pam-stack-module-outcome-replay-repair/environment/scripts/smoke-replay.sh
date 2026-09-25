#!/usr/bin/env bash
# Quick single-fixture smoke check — use instead of replaying the full catalog during edits.
set -euo pipefail

APP="${PAMREPLAY_APP_ROOT:-/app}"
export PAMREPLAY_APP_ROOT="${APP}"
export PAMREPLAY_STACKS_ROOT="${APP}/fixtures/stacks"

bash "${APP}/scripts/reset-state.sh"
"${APP}/bin/pamreplay" replay \
  --stack "${APP}/fixtures/stacks/001-basic-login.json" \
  --user "smoke-user" \
  --export "${APP}/output/smoke-basic-login.json"
echo "smoke replay ok: ${APP}/output/smoke-basic-login.json"
