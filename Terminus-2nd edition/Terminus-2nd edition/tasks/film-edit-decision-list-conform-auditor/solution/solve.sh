#!/usr/bin/env bash
# Oracle: restore conform policy flags and reinstall corrected library modules.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

apply_drop_frame_fix() {
  sed -i 's/^DROP_FRAME_LINEAR=1$/DROP_FRAME_LINEAR=0/' "/app/lib/tc_policy.sh"
}

apply_alias_fix() {
  sed -i 's/^ALIAS_BIDIRECTIONAL=0$/ALIAS_BIDIRECTIONAL=1/' "/app/lib/tc_policy.sh"
}

apply_missing_media_fix() {
  sed -i 's/^MISSING_BEFORE_ALIAS=1$/MISSING_BEFORE_ALIAS=0/' "/app/lib/tc_policy.sh"
}

apply_pulldown_fix() {
  sed -i 's/^PULLDOWN_NUMERATOR=24000$/PULLDOWN_NUMERATOR=23976/' "/app/lib/tc_policy.sh"
}

apply_digest_fix() {
  sed -i 's/^DIGEST_INCLUDES_FINDINGS=0$/DIGEST_INCLUDES_FINDINGS=1/' "/app/lib/tc_policy.sh"
}

apply_emit_guard_fix() {
  sed -i 's/^EMIT_REOPEN=1$/EMIT_REOPEN=0/' "/app/lib/tc_policy.sh"
}

apply_module_patches() {
  patch -p0 -d "${APP_ROOT}" < files/handle_math.sh.patch
  patch -p0 -d "${APP_ROOT}" < files/offline_media_ledger.sh.patch
  patch -p0 -d "${APP_ROOT}" < files/seal_policy.sh.patch
}

main() {
  cd "$(dirname "$0")"
  apply_drop_frame_fix
  apply_alias_fix
  apply_missing_media_fix
  apply_pulldown_fix
  apply_digest_fix
  apply_emit_guard_fix
  apply_module_patches
  sed -i 's/DROP_FRAME_LINEAR=1/DROP_FRAME_LINEAR=0/' "/app/lib/tc_policy.sh"
  sed -i 's/ALIAS_BIDIRECTIONAL=0/ALIAS_BIDIRECTIONAL=1/' "/app/lib/tc_policy.sh"
  bash "${APP_ROOT}/scripts/rebuild-edl-conform-audit.sh"
}

main "$@"
echo "edl-conform-audit oracle applied"
