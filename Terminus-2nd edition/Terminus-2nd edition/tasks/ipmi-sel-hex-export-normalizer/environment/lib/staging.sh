#!/usr/bin/env bash
# Staging snapshot writer for ingest runs.
set -euo pipefail

write_stage_snapshot() {
  local out="$1"
  local accepted="$2"
  local rejected="$3"
  local dup="$4"
  local digest="$5"
  python3 - "${out}" "${accepted}" "${rejected}" "${dup}" "${digest}" <<'PY'
import json, sys
out, acc, rej, dup, dig = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
doc = {
    "accepted": acc,
    "duplicate_rejected": dup,
    "ingest_digest": dig,
    "rejected_checksum": rej,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY
}

record_exists() {
  local db="$1"
  local rid="$2"
  local cnt
  cnt="$(sqlite3 "${db}" "SELECT COUNT(*) FROM sel_records WHERE record_id=${rid};")"
  [ "${cnt}" -gt 0 ]
}

insert_sel_record() {
  local db="$1"
  local rid="$2"
  local rtype="$3"
  local ts="$4"
  local gen="$5"
  local stype="$6"
  local snum="$7"
  local etype="$8"
  local sev="$9"
  local sname="${10}"
  sqlite3 "${db}" "INSERT INTO sel_records (record_id, record_type, ts, generator_id, sensor_type, sensor_number, event_type, severity, sensor_name) VALUES (${rid}, ${rtype}, ${ts}, ${gen}, ${stype}, ${snum}, ${etype}, '${sev}', '${sname}');"
}
