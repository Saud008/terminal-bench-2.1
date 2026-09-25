#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/lattice /app/timeline /app/peers /app/reports /app/runloop /app/model /app/decoy /app/src -name '*.rs' -exec sed -i 's/\r$//' {} +

require_grep() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! grep -qE "${pattern}" "${file}"; then
    echo "oracle preflight missing ${label} in ${file}" >&2
    exit 1
  fi
}

preflight_stubs() {
  require_grep /app/lattice/rtl_ms.rs 'half_life_ms / 1000' 'horizon stub'
  require_grep /app/peers/rtl_pick.rs 'flap_count > 0' 'slot filter stub'
  require_grep /app/runloop/rtl_anchor.rs 'peer_max_ts.max' 'anchor stub'
  require_grep /app/timeline/rtl_digest.rs 'reuse_threshold}"' 'short digest stub'
  require_grep /app/reports/rtl_jsonl.rs 'a\.prefix\.cmp' 'forecast sort stub'
  require_grep /app/src/rdamp_main.rs 'emit-reuse-forecast' 'forecast CLI verb'
}

install_patches() {
  cp "${ROOT_DIR}/files/lattice/rtl_ms.rs" /app/lattice/rtl_ms.rs
  cp "${ROOT_DIR}/files/peers/rtl_pick.rs" /app/peers/rtl_pick.rs
  cp "${ROOT_DIR}/files/runloop/rtl_anchor.rs" /app/runloop/rtl_anchor.rs
  cp "${ROOT_DIR}/files/timeline/rtl_digest.rs" /app/timeline/rtl_digest.rs
  sed -i -f "${ROOT_DIR}/patches/rtl_jsonl_sort.sed" /app/reports/rtl_jsonl.rs
}

postflight() {
  require_grep /app/lattice/rtl_ms.rs 'half_life_ms \+ mid' 'integer horizon'
  require_grep /app/peers/rtl_pick.rs 'peak_penalty >= row.reuse_threshold' 'retention filter'
  require_grep /app/runloop/rtl_anchor.rs 'slot\.last_ts_ms' 'slot anchor'
  require_grep /app/timeline/rtl_digest.rs 'ms_to_reuse' 'digest includes ms_to_reuse'
  require_grep /app/timeline/rtl_digest.rs 'forecast_anchor_ms' 'digest includes forecast_anchor_ms'
  require_grep /app/reports/rtl_jsonl.rs 'peer_id\.cmp' 'peer then prefix sort'
}

preflight_stubs
install_patches
postflight

test -s /app/lattice/rtl_ms.rs
test -s /app/peers/rtl_pick.rs
test -s /app/runloop/rtl_anchor.rs
test -s /app/timeline/rtl_digest.rs
test -s /app/reports/rtl_jsonl.rs
