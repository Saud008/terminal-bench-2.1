"""Writes every keystroke batch of each trajectory run to _reports/<slug>/cmds/run-0N.txt."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SLUG = "cookiejar-rfc6265-repair"
OUT = ROOT / "_reports" / SLUG / "cmds"
OUT.mkdir(parents=True, exist_ok=True)

for run in sorted((ROOT / SLUG / "trajectories").glob("run-0*")):
    t = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    lines = []
    for step in t["steps"]:
        for call in step.get("tool_calls") or []:
            ks = call.get("arguments", {}).get("keystrokes")
            if ks is None:
                ks = json.dumps(call.get("arguments"))
            lines.append(f"### step {step['step_id']} {call['tool_call_id']}\n{ks}")
    (OUT / f"{run.name}.txt").write_text("\n".join(lines), encoding="utf-8")
    ver = (run / "verifier" / "test-stdout.txt").read_text(encoding="utf-8", errors="replace")
    passed = [l for l in ver.splitlines() if l.startswith(("PASSED", "FAILED"))]
    print(run.name, len(lines), "calls;", sum(l.startswith("FAILED") for l in passed), "failed")
sys.exit(0)
