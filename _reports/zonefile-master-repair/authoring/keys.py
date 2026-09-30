"""Print full keystrokes of a run's step(s): keys.py run-01 STEP [STEP...]."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3] / "zonefile-master-repair" / "trajectories"
traj = json.loads((root / sys.argv[1] / "agent" / "trajectory.json").read_text(encoding="utf-8"))
for st in sys.argv[2:]:
    s = traj["steps"][int(st)]
    for tc in s.get("tool_calls") or []:
        k = (tc.get("arguments") or {}).get("keystrokes") or ""
        print(f"--- step {st}\n{k}")
