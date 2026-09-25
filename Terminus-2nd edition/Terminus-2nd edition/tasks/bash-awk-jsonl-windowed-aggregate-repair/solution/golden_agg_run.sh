#!/usr/bin/env bash
# Golden agg-run wrapper — do not ship in environment image.
set -euo pipefail

ROOT="/app"
STATE_DIR="${ROOT}/state"
stream_dir=""
config_path="${ROOT}/config/window.json"
output_path="${ROOT}/output/aggregate-report.json"
accepted_path="${STATE_DIR}/accepted.ndjson"
stats_path="${STATE_DIR}/ingest-stats.json"
rollup_path="${STATE_DIR}/bucket-rollup.ndjson"
manifest_path="${STATE_DIR}/ledger-manifest.json"
run_seq_path="${STATE_DIR}/run-seq.json"

usage() {
  echo "usage: agg-run --stream-dir <dir> [--config path] [--output path]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stream-dir)
      stream_dir="$2"
      shift 2
      ;;
    --config)
      config_path="$2"
      shift 2
      ;;
    --output)
      output_path="$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z "${stream_dir}" || ! -d "${stream_dir}" ]]; then
  echo "agg-run: missing or unreadable stream dir: ${stream_dir}" >&2
  exit 1
fi

window_sec="$(python3 - "${config_path}" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
print(int(doc["window_sec"]))
PY
)"

mkdir -p "$(dirname "${output_path}")" "${STATE_DIR}"
: >"${accepted_path}"
rm -f "${rollup_path}" "${manifest_path}"

mapfile -t files < <(find "${stream_dir}" -type f -name '*.jsonl' | LC_ALL=C sort)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "agg-run: no jsonl files under ${stream_dir}" >&2
  exit 1
fi

input_fingerprint="$(find "${stream_dir}" -type f -name '*.jsonl' -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"

export TZ=UTC
gawk -f "${ROOT}/lib/ingest.awk" \
  -v accepted_path="${accepted_path}" \
  -v stats_path="${stats_path}" \
  "${files[@]}"

accepted_sha256="$(sha256sum "${accepted_path}" | awk '{print $1}')"
events_accepted="$(python3 - "${stats_path}" <<'PY'
import json, sys
print(int(json.load(open(sys.argv[1], encoding="utf-8"))["events_accepted"]))
PY
)"
printf '{"manifest_version":1,"accepted_sha256":"%s","events_accepted":%s}\n' \
  "${accepted_sha256}" "${events_accepted}" >"${manifest_path}"

gawk -f "${ROOT}/lib/bucket.awk" \
  -v window_sec="${window_sec}" \
  -v rollup_path="${rollup_path}" \
  "${accepted_path}"

run_seq="1"
stored_fp=""
if [[ -f "${run_seq_path}" ]]; then
  read -r run_seq stored_fp < <(python3 - "${run_seq_path}" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
print(int(doc.get("seq", 1)), doc.get("input_fingerprint", ""))
PY
)
  if [[ "${stored_fp}" != "${input_fingerprint}" ]]; then
    run_seq=$((run_seq + 1))
  fi
fi

gawk -f "${ROOT}/lib/export.awk" \
  -v window_sec="${window_sec}" \
  -v output="${output_path}" \
  -v stats_path="${stats_path}" \
  -v manifest_path="${manifest_path}" \
  -v accepted_path="${accepted_path}" \
  -v run_seq="${run_seq}" \
  "${rollup_path}"

printf '{"seq": %s, "input_fingerprint": "%s"}\n' "${run_seq}" "${input_fingerprint}" >"${run_seq_path}"

exit 0
