#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

require_oracle_file() {
  local path="$1"
  if [ ! -f "${path}" ]; then
    echo "oracle bundle missing: ${path}" >&2
    exit 1
  fi
}

assert_non_empty_target() {
  local path="$1"
  if [ ! -s "${path}" ]; then
    echo "oracle install produced empty target: ${path}" >&2
    exit 1
  fi
}

normalize_py_tree() {
  find /app/lib/snapret -type f -name '*.py' -exec sed -i 's/\r$//' {} +
}

normalize_py_tree

require_oracle_file "${FILES_DIR}/claim_bind.py"
install -m 0644 "${FILES_DIR}/claim_bind.py" /app/lib/snapret/claim_bind.py
assert_non_empty_target /app/lib/snapret/claim_bind.py

require_oracle_file "${FILES_DIR}/sc_days.py"
install -m 0644 "${FILES_DIR}/sc_days.py" /app/lib/snapret/sc_days.py
assert_non_empty_target /app/lib/snapret/sc_days.py

require_oracle_file "${FILES_DIR}/orph_probe.py"
install -m 0644 "${FILES_DIR}/orph_probe.py" /app/lib/snapret/orph_probe.py
assert_non_empty_target /app/lib/snapret/orph_probe.py

require_oracle_file "${FILES_DIR}/bp_rank.py"
install -m 0644 "${FILES_DIR}/bp_rank.py" /app/lib/snapret/bp_rank.py
assert_non_empty_target /app/lib/snapret/bp_rank.py

require_oracle_file "${FILES_DIR}/ns_rollup.py"
install -m 0644 "${FILES_DIR}/ns_rollup.py" /app/lib/snapret/ns_rollup.py
assert_non_empty_target /app/lib/snapret/ns_rollup.py

require_oracle_file "${FILES_DIR}/vol_report.py"
install -m 0644 "${FILES_DIR}/vol_report.py" /app/lib/snapret/vol_report.py
assert_non_empty_target /app/lib/snapret/vol_report.py

require_oracle_file "${FILES_DIR}/fleet_store.py"
install -m 0644 "${FILES_DIR}/fleet_store.py" /app/lib/snapret/fleet_store.py
assert_non_empty_target /app/lib/snapret/fleet_store.py

require_oracle_file "${FILES_DIR}/analyze_pass.py"
install -m 0644 "${FILES_DIR}/analyze_pass.py" /app/lib/snapret/analyze_pass.py
assert_non_empty_target /app/lib/snapret/analyze_pass.py

if ! grep -q 'audit_pass_seq.*+ 1' /app/lib/snapret/analyze_pass.py; then
  echo "analyze pass counter patch missing" >&2
  exit 1
fi
