#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE="${ROOT_DIR}/files/oracle"

ORACLE_MANIFEST=(
  "lib/rspamd/rotate.sh:0755"
  "lib/rspamd/fuzzy_index.sh:0755"
  "lib/rspamd/console_parse.sh:0755"
  "lib/rspamd/snapshot/publish.sh:0755"
  "lib/rspamd/state_writer.sh:0755"
  "lib/rspamd/shingles.awk:0644"
  "lib/zxq/qvx_lane.sh:0755"
  "lib/zxq/ntx_fold.sh:0755"
  "lib/zxq/pwk_stub.sh:0755"
  "lib/zxq/kzm_guard.sh:0755"
)

require_oracle_sources() {
  local entry rel src
  local missing=0
  for entry in "${ORACLE_MANIFEST[@]}"; do
    rel="${entry%%:*}"
    src="${ORACLE}/${rel}"
    if [[ ! -f "${src}" ]]; then
      echo "oracle missing ${rel}" >&2
      missing=1
    fi
  done
  if [[ "${missing}" -ne 0 ]]; then
    return 1
  fi
  return 0
}

require_oracle_sources

install -D -m 0755 "${ORACLE}/lib/rspamd/rotate.sh" /app/lib/rspamd/rotate.sh
install -D -m 0755 "${ORACLE}/lib/rspamd/fuzzy_index.sh" /app/lib/rspamd/fuzzy_index.sh
install -D -m 0755 "${ORACLE}/lib/rspamd/console_parse.sh" /app/lib/rspamd/console_parse.sh
install -D -m 0755 "${ORACLE}/lib/rspamd/snapshot/publish.sh" /app/lib/rspamd/snapshot/publish.sh
install -D -m 0755 "${ORACLE}/lib/rspamd/state_writer.sh" /app/lib/rspamd/state_writer.sh
install -D -m 0644 "${ORACLE}/lib/rspamd/shingles.awk" /app/lib/rspamd/shingles.awk
install -D -m 0755 "${ORACLE}/lib/zxq/qvx_lane.sh" /app/lib/zxq/qvx_lane.sh
install -D -m 0755 "${ORACLE}/lib/zxq/ntx_fold.sh" /app/lib/zxq/ntx_fold.sh
install -D -m 0755 "${ORACLE}/lib/zxq/pwk_stub.sh" /app/lib/zxq/pwk_stub.sh
install -D -m 0755 "${ORACLE}/lib/zxq/kzm_guard.sh" /app/lib/zxq/kzm_guard.sh

find /app/lib -type f \( -name '*.sh' -o -name '*.awk' \) -exec sed -i 's/\r$//' {} +
chmod +x /app/bin/rspamd-fuzzy-audit /app/lib/rspamd/*.sh /app/lib/rspamd/snapshot/*.sh /app/lib/zxq/*.sh /app/scripts/*.sh
bash /app/scripts/reset-state.sh
