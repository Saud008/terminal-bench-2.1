#!/usr/bin/env bash
# Exit-code aggregation for manifests and exports.
set -euo pipefail

is_success_exit() {
  local code="$1"
  [ "${code}" -eq 0 ]
}

exit_histogram_from_db() {
  python3 - "${MANIFEST_DB}" <<'PY'
import json, sqlite3, sys
db = sys.argv[1]
conn = sqlite3.connect(db)
hist = {}
for (exitval,) in conn.execute("SELECT exitval FROM jobs ORDER BY seq"):
    key = str(int(exitval))
    hist[key] = hist.get(key, 0) + 1
conn.close()
print(json.dumps(hist, sort_keys=True, separators=(",", ":")))
PY
}

failed_exit_count_from_db() {
  local failed=0 exitval
  while read -r exitval; do
    [ -n "${exitval}" ] || continue
    if ! is_success_exit "${exitval}"; then
      failed=$((failed + 1))
    fi
  done < <(sqlite3 "${MANIFEST_DB}" "SELECT exitval FROM jobs;")
  echo "${failed}"
}

joblog_exit_histogram() {
  local joblog="$1"
  python3 - "${joblog}" <<'PY'
import json, sys
from pathlib import Path
rows = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
hist = {}
for line in rows[1:]:
    parts = line.split("\t")
    if len(parts) < 9:
        continue
    key = str(int(parts[6]))
    hist[key] = hist.get(key, 0) + 1
print(json.dumps(hist, sort_keys=True, separators=(",", ":")))
PY
}

manifest_exit_histogram() {
  local joblog="$1"
  local par_dir="$2"
  python3 - "${joblog}" "${par_dir}" <<'PY'
import json, sys
from pathlib import Path
joblog = Path(sys.argv[1])
par_dir = Path(sys.argv[2])
pars = {}
for par in par_dir.glob("*.par"):
    data = {}
    for line in par.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    if "seq" in data:
        pars[int(data["seq"])] = int(data.get("exit", 0))
hist = {}
for line in joblog.read_text(encoding="utf-8").splitlines()[1:]:
    parts = line.split("\t")
    if len(parts) < 9:
        continue
    seq = int(parts[0])
    code = pars.get(seq, int(parts[6]))
    key = str(code)
    hist[key] = hist.get(key, 0) + 1
print(json.dumps(hist, sort_keys=True, separators=(",", ":")))
PY
}
