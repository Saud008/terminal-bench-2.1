#!/usr/bin/env bash
# Merge per-file NDJSON rows into final tick index JSON.

sd_export_index() {
  local seed="$1"
  local files_list="$2"
  local rows_ndjson="$3"
  local out_json="$4"

  python3 - <<'PY' "$seed" "$files_list" "$rows_ndjson" "$out_json"
import json, sys
from collections import defaultdict
from pathlib import Path

seed = sys.argv[1]
files = [ln.strip() for ln in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if ln.strip()]
rows_path = Path(sys.argv[3])
out_path = Path(sys.argv[4])

by_tick: dict[tuple[int, str], list[dict]] = defaultdict(list)
signon_resets = 0
usercmd_total = 0

if rows_path.is_file():
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        key = (rec["global_tick"], rec["source"])
        by_tick[key].append(
            {
                "seq": rec["seq"],
                "str_idx": rec["str_idx"],
                "string": rec["string"],
                "arg": rec["arg"],
            }
        )
        usercmd_total += 1

ticks = []
for (gtick, source) in sorted(by_tick.keys()):
    cmds = sorted(by_tick[(gtick, source)], key=lambda c: c["seq"])
    ticks.append({"global_tick": gtick, "source": source, "usercmds": cmds})

doc = {
    "index_version": 1,
    "seed": seed,
    "files": files,
    "ticks": ticks,
    "stats": {
        "file_count": len(files),
        "tick_count": len(ticks),
        "usercmd_count": usercmd_total,
        "signon_resets": signon_resets,
    },
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}
