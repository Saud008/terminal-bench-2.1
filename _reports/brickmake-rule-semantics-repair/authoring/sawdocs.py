"""sawdocs.py <trial-dir>...: did the agent read docs/rules.md and see the 'No rule to make target' sentence?"""
import json
import sys
from pathlib import Path

NEEDLE = "if it has none and does not exist, the build then fails"
for d in sys.argv[1:]:
    traj = json.loads((Path(d) / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    steps = traj.get("steps", [])
    read_cmd, seen = None, None
    for i, s in enumerate(steps):
        blob = json.dumps(s)
        if read_cmd is None and "rules.md" in blob and ("cat " in blob or "sed " in blob):
            read_cmd = i
        if seen is None and NEEDLE in blob:
            seen = i
    print(f"{Path(d).name}: steps={len(steps)} first rules.md read at step {read_cmd}, sentence seen at step {seen}")
