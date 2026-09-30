import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
cap = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
out.mkdir(parents=True, exist_ok=True)
for run in sorted(root.glob("run-*")):
    d = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    lines = []
    for s in d["steps"]:
        if s.get("source") != "agent":
            continue
        for tc in s.get("tool_calls") or []:
            ks = (tc.get("arguments") or {}).get("keystrokes")
            if ks is None:
                ks = json.dumps(tc.get("arguments"))
            if len(ks) > cap:
                ks = ks[:cap] + f"...[+{len(ks) - cap} chars]"
            lines.append(f"[step {s['step_id']}] {ks.rstrip()}")
    (out / f"{run.name}_cmds.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(run.name, len(lines))
