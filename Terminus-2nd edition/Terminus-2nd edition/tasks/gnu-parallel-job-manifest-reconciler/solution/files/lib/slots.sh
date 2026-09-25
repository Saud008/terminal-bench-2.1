#!/usr/bin/env bash
# Peak slot / concurrency helpers.
set -euo pipefail

peak_concurrency_from_pardir() {
  local par_dir="$1"
  python3 - "${par_dir}" <<'PY'
import sys
from pathlib import Path
par_dir = Path(sys.argv[1])
events = []
for par in par_dir.glob("*.par"):
    data = {}
    for line in par.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    if "start_epoch" not in data or "end_epoch" not in data:
        continue
    start = float(data["start_epoch"])
    end = float(data["end_epoch"])
    events.append((start, 1))
    events.append((end, -1))
if not events:
    print(0)
    raise SystemExit
events.sort(key=lambda t: (t[0], -t[1]))
running = 0
peak = 0
for _ts, delta in events:
    running += delta
    peak = max(peak, running)
print(peak)
PY
}

peak_concurrency_from_db() {
  peak_concurrency_from_pardir "${PAR_DIR_FOR_EXPORT:-/app/fixtures/seed/par}"
}
