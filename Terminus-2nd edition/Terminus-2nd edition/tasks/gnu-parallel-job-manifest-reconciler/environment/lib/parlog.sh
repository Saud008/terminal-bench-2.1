#!/usr/bin/env bash
# Parse per-job .par profiler logs (key=value lines).
set -euo pipefail

par_file_count() {
  local par_dir="$1"
  find "${par_dir}" -maxdepth 1 -type f -name '*.par' | wc -l | tr -d ' '
}

parse_par_kv() {
  local par_file="$1"
  local key="$2"
  awk -F= -v k="${key}" '$1 == k { print $2; exit }' "${par_file}"
}

merge_par_into_db() {
  local par_dir="$1"
  local par_file seq slot exit utime stime wall start end
  for par_file in "${par_dir}"/*.par; do
    [ -f "${par_file}" ] || continue
    seq="$(parse_par_kv "${par_file}" seq)"
    slot="$(parse_par_kv "${par_file}" slot)"
    exit="$(parse_par_kv "${par_file}" exit)"
    utime="$(parse_par_kv "${par_file}" utime_jiffies)"
    stime="$(parse_par_kv "${par_file}" stime_jiffies)"
    wall="$(parse_par_kv "${par_file}" wall_sec)"
    start="$(parse_par_kv "${par_file}" start_epoch)"
    end="$(parse_par_kv "${par_file}" end_epoch)"
    [ -n "${seq}" ] || continue
    sqlite3 "${MANIFEST_DB}" <<SQL
UPDATE jobs SET
  exitval = ${exit},
  slot = ${slot},
  utime_jiffies = ${utime},
  stime_jiffies = ${stime},
  wall_sec = ${wall},
  start_epoch = ${start},
  end_epoch = ${end}
WHERE seq = ${seq};
SQL
  done
}

par_exit_histogram() {
  local par_dir="$1"
  python3 - "${par_dir}" <<'PY'
import json, sys
from pathlib import Path
par_dir = Path(sys.argv[1])
hist = {}
for par in sorted(par_dir.glob("*.par")):
    data = {}
    for line in par.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    if "exit" not in data:
        continue
    key = str(int(data["exit"]))
    hist[key] = hist.get(key, 0) + 1
print(json.dumps(hist, sort_keys=True, separators=(",", ":")))
PY
}

par_cpu_seconds_total() {
  local par_dir="$1"
  python3 - "${par_dir}" "${USER_HZ}" <<'PY'
import sys
from pathlib import Path
par_dir = Path(sys.argv[1])
hz = int(sys.argv[2])
total = 0.0
for par in par_dir.glob("*.par"):
    data = {}
    for line in par.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    ut = int(data.get("utime_jiffies", 0))
    st = int(data.get("stime_jiffies", 0))
    total += (ut + st) / hz
print(f"{total:.6f}")
PY
}
