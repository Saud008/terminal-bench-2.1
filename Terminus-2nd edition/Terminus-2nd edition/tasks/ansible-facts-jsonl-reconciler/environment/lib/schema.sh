#!/usr/bin/env bash
# Staging schema validation helpers.
set -euo pipefail

validate_staging_schema() {
  local path="$1"
  local run_id="$2"
  python3 - "${path}" "${FACTS_DB}" "${run_id}" <<'PY'
import json, sqlite3, sys
path, db_path, run_id = sys.argv[1], sys.argv[2], sys.argv[3]
doc = json.loads(open(path, encoding="utf-8").read())
conn = sqlite3.connect(db_path)
hosts = conn.execute(
    "SELECT h.inventory_uuid, h.hostname, COUNT(f.fact_key) "
    "FROM hosts h JOIN fact_snapshots f ON f.inventory_uuid = h.inventory_uuid "
    "GROUP BY h.inventory_uuid ORDER BY h.inventory_uuid"
).fetchall()
expected_hosts = [
    {"inventory_uuid": u, "hostname": h, "fact_count": c} for u, h, c in hosts
]
if doc.get("run_id") != run_id:
    raise SystemExit("run_id mismatch")
if doc.get("hosts") != expected_hosts:
    raise SystemExit("hosts mismatch")
total = sum(h["fact_count"] for h in expected_hosts)
if doc.get("total_fact_keys") != total:
    raise SystemExit("total_fact_keys mismatch")
snap_total = conn.execute("SELECT COUNT(*) FROM fact_snapshots").fetchone()[0]
if total != snap_total:
    raise SystemExit("internal total mismatch")
src = conn.execute(
    "SELECT COALESCE((SELECT source_lines FROM run_meta WHERE run_id = ?), 0)",
    (run_id,),
).fetchone()[0]
if doc.get("source_lines") != src:
    raise SystemExit("source_lines mismatch")
PY
}

build_staging_document() {
  local run_id="$1"
  python3 - "${FACTS_DB}" "${run_id}" <<'PY'
import json, sqlite3, sys
db_path, run_id = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db_path)
hosts = []
for row in conn.execute(
    "SELECT h.inventory_uuid, h.hostname, COUNT(f.fact_key) "
    "FROM hosts h JOIN fact_snapshots f ON f.inventory_uuid = h.inventory_uuid "
    "GROUP BY h.inventory_uuid ORDER BY h.inventory_uuid"
):
    hosts.append({"inventory_uuid": row[0], "hostname": row[1], "fact_count": row[2]})
total = conn.execute("SELECT COUNT(*) FROM fact_snapshots").fetchone()[0]
src = conn.execute(
    "SELECT COALESCE((SELECT source_lines FROM run_meta WHERE run_id = ?), 0)",
    (run_id,),
).fetchone()[0]
doc = {
    "run_id": run_id,
    "hosts": hosts,
    "total_fact_keys": total,
    "source_lines": src,
}
print(json.dumps(doc, sort_keys=True, separators=(",", ":")))
PY
}
