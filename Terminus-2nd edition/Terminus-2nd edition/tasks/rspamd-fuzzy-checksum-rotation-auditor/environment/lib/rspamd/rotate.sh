#!/usr/bin/env bash
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${LIB}/common.sh"
# shellcheck source=fuzzy_index.sh
source "${LIB}/fuzzy_index.sh"
# shellcheck source=console_parse.sh
source "${LIB}/console_parse.sh"
# shellcheck source=state_writer.sh
source "${LIB}/state_writer.sh"
# shellcheck source=snapshot/publish.sh
source "${LIB}/snapshot/publish.sh"

rf_rotate_run() {
  local corpus_dir="$1"
  local key_manifest="$2"
  local window_size="$3"
  local console_dump="$4"
  local dry_run="$5"
  local summary_path="$6"

  local manifest="${corpus_dir%/}/mails.tsv"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap "rm -rf '${tmp_dir}'" RETURN

  local key_epoch checksum_algo_id epoch_salt salt_suffix
  read -r key_epoch checksum_algo_id epoch_salt < <(python3 - "${key_manifest}" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
print(m["key_epoch"], m["checksum_algo_id"], m["epoch_salt"])
PY
)
  salt_suffix="${RF_EPOCH_SALT_SUFFIX:-}"
  local effective_salt="${epoch_salt}${salt_suffix}"

  rf_publish_shingle_snapshot "${manifest}" "${effective_salt}"

  if [[ -f "${corpus_dir}/seed.sql" && "${dry_run}" != "true" ]]; then
    rf_ensure_index
    sqlite3 "${RF_INDEX_DB}" < "${corpus_dir}/seed.sql"
  fi

  if [[ "${dry_run}" != "true" ]]; then
    rf_index_rotate_epoch "${key_epoch}" "${checksum_algo_id}"
  fi

  rf_require_cmd gawk
  local mail_count=0
  : > "${tmp_dir}/bodies.tsv"
  while IFS=$'\t' read -r mail_id eml_file; do
    [[ -z "${mail_id}" ]] && continue
    mail_count=$((mail_count + 1))
    local eml_path="${corpus_dir%/}/${eml_file}"
    python3 - "${eml_path}" "${mail_id}" "${window_size}" \
      "${key_epoch}" "${checksum_algo_id}" "${tmp_dir}/bodies.tsv" <<'PY' >> "${tmp_dir}/bodies.tsv"
import hashlib
import re
import sys
from pathlib import Path

eml_path, mail_id, window, ke, algo, _ = sys.argv[1:6]
raw = Path(eml_path).read_text(encoding="utf-8")
parts = raw.split("\n\n", 1)
body = parts[1] if len(parts) > 1 else raw
body = re.sub(r"\s+", " ", body.lower()).strip()
print(f"{mail_id}\t{body}")
PY
  done < <(rf_read_manifest "${manifest}")

  gawk -f "${LIB}/shingles.awk" -v window_size="${window_size}" \
    "${tmp_dir}/bodies.tsv" > "${tmp_dir}/shingles.tsv"

  if [[ "${dry_run}" != "true" ]]; then
    while IFS=$'\t' read -r mid shingle; do
      [[ -z "${mid}" ]] && continue
      local digest
      digest="$(python3 - "${key_epoch}" "${checksum_algo_id}" "${shingle}" <<'PY'
import hashlib, sys
ke, algo, sh = sys.argv[1:4]
print(hashlib.sha256(f"{ke}:{algo}:{sh}".encode()).hexdigest()[:16])
PY
)"
      rf_index_insert_shingle "${digest}" "${mid}" "${shingle}" "${key_epoch}" "${checksum_algo_id}"
    done < "${tmp_dir}/shingles.tsv"
  fi

    gawk -f "${LIB}/summary/rollup.awk" \
    -v out_path="${tmp_dir}/summary_counts.txt" \
    "${tmp_dir}/shingles.tsv"

  local unique_shingles total_rows
  unique_shingles="$(sed -n '1p' "${tmp_dir}/summary_counts.txt")"
  total_rows="$(sed -n '2p' "${tmp_dir}/summary_counts.txt")"

  local console_matched=0
  if [[ "${dry_run}" != "true" ]]; then
    if ! console_matched="$(rf_console_verify "${console_dump}" "${key_epoch}" "${checksum_algo_id}" "${RF_INDEX_DB}")"; then
      echo "console verification failed" >&2
      exit 1
    fi
  else
    console_matched="$(wc -l < "${console_dump}" | tr -d ' ')"
  fi

  python3 - "${key_epoch}" "${checksum_algo_id}" "${mail_count}" \
    "${unique_shingles}" "${total_rows}" "${console_matched}" "${dry_run}" "${summary_path}" <<'PY'
import json
import sys
from pathlib import Path

ke, algo, mails, uniq, rows, console, dry, summary_path = sys.argv[1:9]
doc = {
    "schema": 1,
    "key_epoch": int(ke),
    "checksum_algo_id": int(algo),
    "mails_processed": int(mails),
    "unique_shingles": int(uniq),
    "total_shingle_rows": int(rows),
    "console_lines_matched": int(console),
    "dry_run": dry.lower() == "true",
}
Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
Path(summary_path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  if [[ "${dry_run}" != "true" ]]; then
    rf_write_rotation_run "${key_epoch}" "${checksum_algo_id}" "${mail_count}" \
      "${unique_shingles}" "${total_rows}" "${console_matched}"
  fi
}
