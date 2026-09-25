#!/usr/bin/env bash
set -euo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${LIB}/common.sh"
# shellcheck source=cache_ledger.sh
source "${LIB}/cache_ledger.sh"
# shellcheck source=state_writer.sh
source "${LIB}/state_writer.sh"
# shellcheck source=staging/publish.sh
source "${LIB}/staging/publish.sh"

oi_sync_run() {
  local mailbox_dir="$1"
  local imap_meta="$2"
  local folder_rules="$3"
  local reference_epoch="$4"
  local maxage_sec="$5"
  local tz_offset="$6"
  local dry_run="$7"
  local export_path="$8"

  local manifest="${mailbox_dir%/}/messages.tsv"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap "rm -rf '${tmp_dir}'" RETURN

  local account folders_json
  account="$(python3 - "${imap_meta}" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["account"])
PY
)"
  folders_json="$(python3 - "${imap_meta}" <<'PY'
import json, sys
meta = json.load(open(sys.argv[1], encoding="utf-8"))
rows = [{"name": f["name"], "uidvalidity": f["uidvalidity"], "selected": True} for f in meta["folders"]]
print(json.dumps(rows))
PY
)"

  oi_publish_folder_snapshot "${account}" "${folders_json}"

  while IFS=$'\t' read -r fname fval; do
    oi_ledger_prepare_folder "${fname}" "${fval}"
  done < <(python3 - "${imap_meta}" <<'PY'
import json, sys
meta = json.load(open(sys.argv[1], encoding="utf-8"))
for f in meta["folders"]:
    print(f"{f['name']}\t{f['uidvalidity']}")
PY
)

  oi_require_cmd gawk
  oi_read_manifest "${manifest}" > "${tmp_dir}/raw.tsv"

  gawk -f "${LIB}/maxage.awk" \
    -v reference_epoch="${reference_epoch}" \
    -v maxage_sec="${maxage_sec}" \
    -v stats_path="${tmp_dir}/stats.txt" \
    "${tmp_dir}/raw.tsv" > "${tmp_dir}/aged.tsv"

  gawk -f "${LIB}/folder_filter.awk" \
    -v rules_path="${folder_rules}" \
    "${tmp_dir}/aged.tsv" > "${tmp_dir}/selected.tsv"

  gawk -f "${LIB}/export/summary.awk" \
    -v out_path="${tmp_dir}/summary_counts.txt" \
    "${tmp_dir}/selected.tsv"

  local synced_messages synced_bytes
  synced_messages="$(sed -n '1p' "${tmp_dir}/summary_counts.txt")"
  synced_bytes="$(sed -n '2p' "${tmp_dir}/summary_counts.txt")"

  python3 - "${account}" "${reference_epoch}" "${maxage_sec}" "${tz_offset}" \
    "${dry_run}" "${synced_messages}" "${synced_bytes}" "${export_path}" \
    "${tmp_dir}/selected.tsv" <<'PY'
import json
import sys
from pathlib import Path

account, ref, maxage, tz, dry, msgs, byts, export_path, sel_path = sys.argv[1:10]
folders = sorted({line.split("\t", 1)[0] for line in Path(sel_path).read_text(encoding="utf-8").splitlines() if line.strip()})
cutoff = int(ref) - int(maxage)
doc = {
    "schema": 1,
    "account": account,
    "reference_epoch": int(ref),
    "maxage_sec": int(maxage),
    "tz_offset": int(tz),
    "dry_run": dry.lower() == "true",
    "synced_messages": int(msgs),
    "synced_bytes": int(byts),
    "folders": folders,
    "cutoff_utc": cutoff,
}
Path(export_path).parent.mkdir(parents=True, exist_ok=True)
Path(export_path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  oi_write_sync_run "${account}" "${reference_epoch}" "${synced_messages}" "${synced_bytes}" "${dry_run}"

  if [[ "${dry_run}" != "true" ]]; then
    while IFS=$'\t' read -r folder _ _ uid; do
      [[ -z "${folder}" ]] && continue
      local prev
      prev="$(oi_ledger_read_high "${folder}" || echo 0)"
      if [[ "${uid}" -gt "${prev}" ]]; then
        oi_ledger_update_high "${folder}" "${uid}"
      fi
    done < "${tmp_dir}/selected.tsv"
  fi
}
