#!/usr/bin/env bash
set -euo pipefail

manifest="$1"
pair_id="$2"
ipt_path="$3"
nft_path="$4"
STATE_DIR="${APP_ROOT:-/app}/state"

source "${APP_ROOT:-/app}/lib/common.sh"

ipt_sha=$(sha256_file "${ipt_path}")
nft_sha=$(sha256_file "${nft_path}")
fp=$(pair_fingerprint "${manifest}" "${ipt_path}" "${nft_path}")
ipt_count=$(wc -l < "${STATE_DIR}/iptables-tuples.ndjson" | tr -d ' ')
nft_count=$(wc -l < "${STATE_DIR}/nft-tuples.ndjson" | tr -d ' ')
policy=$(cat "${STATE_DIR}/policy_precedence.json")
unsupported=$(cat "${STATE_DIR}/unsupported.json")

# digest currently hashes iptables tuples only
digest=$(sha256_file "${STATE_DIR}/iptables-tuples.ndjson")

python3 <<PY
import json
meta = {
  "pair_id": "${pair_id}",
  "pair_fingerprint": "${fp}",
  "staging_digest": "${digest}",
  "iptables_sha256": "${ipt_sha}",
  "nft_sha256": "${nft_sha}",
  "tuple_counts": {"iptables": int("${ipt_count}"), "nft": int("${nft_count}")},
  "policy_precedence": json.loads('''${policy}'''),
  "unsupported_features": json.loads('''${unsupported}'''),
}
json.dump(meta, open("${STATE_DIR}/staging-meta.json", "w"), indent=2)
PY
