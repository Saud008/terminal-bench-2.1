#!/usr/bin/env bash
# Diff recording and export helpers.
set -euo pipefail

record_fact_diff() {
  local run_id="$1"
  local inventory_uuid="$2"
  local fact_key="$3"
  local old_value="$4"
  local new_value="$5"
  sqlite3 "${FACTS_DB}" \
    "INSERT INTO fact_diffs (run_id, inventory_uuid, fact_key, old_value, new_value)
     VALUES ('$(printf '%s' "${run_id}" | sed "s/'/''/g")',
             '$(printf '%s' "${inventory_uuid}" | sed "s/'/''/g")',
             '$(printf '%s' "${fact_key}" | sed "s/'/''/g")',
             NULL,
             '$(printf '%s' "${new_value}" | sed "s/'/''/g")');"
}

export_changed_key_count() {
  local run_id="$1"
  snapshot_count
}

export_changed_keys_digest() {
  local run_id="$1"
  python3 - "${FACTS_DB}" "${run_id}" <<'PY'
import hashlib, sqlite3, sys
db_path, run_id = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db_path)
pairs = [
    f"{u}\t{k}"
    for u, k in conn.execute(
        "SELECT inventory_uuid, fact_key FROM fact_diffs WHERE run_id = ? "
        "GROUP BY inventory_uuid, fact_key ORDER BY inventory_uuid, fact_key",
        (run_id,),
    )
]
digest = hashlib.sha256("\n".join(pairs).encode()).hexdigest()
print(digest)
PY
}

export_diff_rows_json() {
  local run_id="$1"
  python3 - "${FACTS_DB}" "${run_id}" <<'PY'
import json, sqlite3, sys
db_path, run_id = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db_path)
rows = []
for u, k, old_v, new_v in conn.execute(
    "SELECT inventory_uuid, fact_key, old_value, new_value FROM fact_diffs "
    "WHERE run_id = ? ORDER BY inventory_uuid, fact_key",
    (run_id,),
):
    rows.append(
        {
            "inventory_uuid": u,
            "fact_key": k,
            "old_value": old_v,
            "new_value": new_v,
        }
    )
print(json.dumps(rows, separators=(",", ":")))
PY
}
