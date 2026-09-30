"""Dump each delivered run's failing cases and numbered agent commands to _reports/.../runs/run-0N.txt."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[3] / "zonefile-master-repair" / "trajectories"
outdir = Path(__file__).resolve().parents[1] / "runs"
outdir.mkdir(exist_ok=True)
for run in sorted(root.glob("run-0*")):
    lines = []
    stdout = (run / "verifier" / "test-stdout.txt").read_text(errors="replace")
    for line in stdout.splitlines():
        if line.startswith(("PASSED", "FAILED")) or re.match(r"E\s+--- ", line):
            lines.append("T " + line[:200])
    traj = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    for i, s in enumerate(traj.get("steps", [])):
        for tc in s.get("tool_calls") or []:
            k = (tc.get("arguments") or {}).get("keystrokes") or ""
            if k.strip():
                lines.append(f"{i:03d}> " + k[:700].replace("\n", " | "))
    (outdir / f"{run.name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(run.name, len(lines))
