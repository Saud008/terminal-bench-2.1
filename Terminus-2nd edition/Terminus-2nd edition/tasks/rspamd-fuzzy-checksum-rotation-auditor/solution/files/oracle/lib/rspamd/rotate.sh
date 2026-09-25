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
    python3 - "${eml_path}" "${mail_id}" <<'PY' >> "${tmp_dir}/bodies.tsv"
import re
import sys
from pathlib import Path

eml_path, mail_id = sys.argv[1:3]
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

  if [[ "${dry_run}" == "true" ]]; then
    read -r unique_shingles total_rows < <(python3 - "${key_epoch}" "${checksum_algo_id}" "${tmp_dir}/shingles.tsv" <<'PY'
import hashlib
import sys
from pathlib import Path

ke, algo, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
hashes: set[str] = set()
total = 0
for line in Path(path).read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    _mid, shingle = line.split("\t", 1)
    total += 1
    digest = hashlib.sha256(f"{ke}:{algo}:{shingle}".encode()).hexdigest()[:16]
    hashes.add(digest)
print(len(hashes), total)
PY
)
  else
    unique_shingles="$(rf_index_distinct_hashes)"
    total_rows="$(rf_index_row_count)"
  fi

  local console_matched=0
  if [[ "${dry_run}" != "true" ]]; then
    if ! console_matched="$(rf_console_verify "${console_dump}" "${key_epoch}" "${checksum_algo_id}" "${RF_INDEX_DB}")"; then
      rf_write_rollback "${key_epoch}" "${checksum_algo_id}" "console_mismatch"
      echo "console verification failed" >&2
      exit 1
    fi
  else
    console_matched="$(python3 - "${console_dump}" <<'PY'
import sys
from pathlib import Path

print(sum(1 for ln in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if ln.strip()))
PY
)"
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
