#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
STATE_DIR="${APP_ROOT}/state"
source "${APP_ROOT}/lib/common.sh"

manifest=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pair) manifest="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ -n "${manifest}" ] && [ -f "${manifest}" ] || exit 2

pair_id=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['pair_id'])" "${manifest}")
ipt_path=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['iptables_path'])" "${manifest}")
nft_path=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['nft_path'])" "${manifest}")

mkdir -p "${STATE_DIR}"

# parse_ipt.awk omits bracket counters on chain policy lines in baseline
gawk -f "${APP_ROOT}/lib/parse_ipt.awk" "${ipt_path}" > "${STATE_DIR}/iptables-tuples.ndjson"
gawk -f "${APP_ROOT}/lib/parse_nft.awk" "${nft_path}" > "${STATE_DIR}/nft-tuples.ndjson"

# normalize_match.awk does not sort ct states or dports in baseline
gawk -f "${APP_ROOT}/lib/normalize_match.awk" "${STATE_DIR}/iptables-tuples.ndjson" > "${STATE_DIR}/.ipt-norm.ndjson"
mv "${STATE_DIR}/.ipt-norm.ndjson" "${STATE_DIR}/iptables-tuples.ndjson"
gawk -f "${APP_ROOT}/lib/normalize_match.awk" "${STATE_DIR}/nft-tuples.ndjson" > "${STATE_DIR}/.nft-norm.ndjson"
mv "${STATE_DIR}/.nft-norm.ndjson" "${STATE_DIR}/nft-tuples.ndjson"

bash "${APP_ROOT}/lib/policy_rank.sh" "${nft_path}" > "${STATE_DIR}/policy_precedence.json"
bash "${APP_ROOT}/lib/unsupported_scan.sh" "${ipt_path}" > "${STATE_DIR}/unsupported.json"

# staging_commit.sh digest excludes nft tuples in baseline
bash "${APP_ROOT}/lib/staging_commit.sh" "${manifest}" "${pair_id}" "${ipt_path}" "${nft_path}"

fp=$(pair_fingerprint "${manifest}" "${ipt_path}" "${nft_path}")
run_seq_file="${STATE_DIR}/run-seq.json"
if [ -f "${run_seq_file}" ]; then
  last_fp=$(python3 -c "import json; print(json.load(open('${run_seq_file}')).get('last_pair_fingerprint',''))")
  run_seq=$(python3 -c "import json; print(json.load(open('${run_seq_file}')).get('run_seq',0))")
  if [ "${last_fp}" != "${fp}" ]; then
    run_seq=$((run_seq + 1))
  fi
else
  run_seq=1
fi
python3 -c "import json; json.dump({'run_seq':${run_seq},'last_pair_fingerprint':'${fp}','pair_id':'${pair_id}'}, open('${run_seq_file}','w'))"

echo "${pair_id}" > "${STATE_DIR}/active-pair.id"
exit 0
