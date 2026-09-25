#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "${SOL}/golden_merge_rules.sh" "${APP_ROOT}/lib/merge_rules.sh"
cp "${SOL}/golden_subject_eval.sh" "${APP_ROOT}/lib/subject_eval.sh"
cp "${SOL}/golden_action_registry.sh" "${APP_ROOT}/lib/action_registry.sh"
cp "${SOL}/golden_challenge.sh" "${APP_ROOT}/lib/challenge.sh"
cp "${SOL}/golden_auth_cache.sh" "${APP_ROOT}/lib/auth_cache.sh"

chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/bin/pkctl"
sed -i 's/\r$//' "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/bin/pkctl" 2>/dev/null || true
bash "${APP_ROOT}/scripts/verifier-rebuild.sh"
echo "pkctl oracle ready"
