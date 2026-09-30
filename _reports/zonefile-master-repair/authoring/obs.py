"""Print a run's step observation: obs.py run-01 STEP [maxchars] [grep]."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3] / "zonefile-master-repair" / "trajectories"
run, step = sys.argv[1], int(sys.argv[2])
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
needle = sys.argv[4] if len(sys.argv) > 4 else None
traj = json.loads((root / run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
s = traj["steps"][step]
obs = s.get("observation") or {}
text = json.dumps(obs) if not isinstance(obs, str) else obs
if isinstance(obs, dict):
    parts = []
    for r in obs.get("results", []):
        parts.append(str(r.get("content", "")))
    text = "\n".join(parts) or text
if needle:
    for line in text.splitlines():
        if needle in line:
            print(line[:300])
else:
    print(text[:limit])
