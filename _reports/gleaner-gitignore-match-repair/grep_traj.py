"""usage: grep_traj.py RUN_DIR REGEX [ctx] -> matches in agent keystrokes (full, untruncated) with step ids."""
import json
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
rx = re.compile(sys.argv[2])
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 90
d = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
for s in d["steps"]:
    if s.get("source") != "agent":
        continue
    for tc in s.get("tool_calls") or []:
        ks = (tc.get("arguments") or {}).get("keystrokes") or ""
        for m in rx.finditer(ks):
            a, b = max(0, m.start() - ctx), min(len(ks), m.end() + ctx)
            print(f"[step {s['step_id']}] ...{ks[a:b]!r}...")
