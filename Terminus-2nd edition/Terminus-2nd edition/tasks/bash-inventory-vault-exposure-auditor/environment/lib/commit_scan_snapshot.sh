#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
source "${APP_ROOT}/lib/common.sh"
manifest="$1"
tree_id="$2"
inventory_root="$3"
host-rows.ndjson="${STATE_DIR}/host-rows.ndjson"
# baseline digest uses hosts file only when DIGEST_FINDINGS is false
digest=$(sha256_file "${host-rows.ndjson}")
fp=$(tree_fingerprint "${manifest}" "${inventory_root}")
python3 <<PY
import json
meta = {
  "tree_id": "${tree_id}",
  "tree_fingerprint": "${fp}",
  "staging_digest": "${digest}",
  "merge_order": json.load(open("${STATE_DIR}/merge-order.json")),
  "host_count": sum(1 for _ in open("${host-rows.ndjson}") if _.strip()),
  "finding_count": sum(1 for _ in open("${STATE_DIR}/atlas-rows.ndjson") if _.strip()) if __import__('pathlib').Path("${STATE_DIR}/atlas-rows.ndjson").is_file() else 0,
}
json.dump(meta, open("${STATE_DIR}/scan-manifest.json", "w"), indent=2)
PY
