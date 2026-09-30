"""Summarise a run_k job: per trial test results, first failure lines, and the agent's commands."""
import json
import sys
from pathlib import Path

job = Path(sys.argv[1])
full = len(sys.argv) > 2
for trial in sorted(p for p in job.iterdir() if p.is_dir()):
    out = trial / "verifier" / "test-stdout.txt"
    if not out.exists():
        continue
    print("=====", trial.name)
    text = out.read_text(errors="replace")
    for line in text.splitlines():
        if line.startswith(("PASSED", "FAILED")):
            print(" ", line[:110])
    if full:
        for line in text.splitlines():
            if line.startswith(("E   ", "--- ", "expected", "got ")):
                print("   |", line[:200])
        traj = json.loads((trial / "agent" / "trajectory.json").read_text())
        for s in traj.get("steps", []):
            for tc in s.get("tool_calls") or []:
                k = (tc.get("arguments") or {}).get("keystrokes") or ""
                if k:
                    print("  >", k[:220].replace("\n", " | "))
