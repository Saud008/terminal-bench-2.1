"""dump_traj.py <trajectories-dir> <out-dir>: per run, a compact list of steps with the commands
sent and a short head/tail of each observation, for hand-grading rubric_score.txt."""
import json
import sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)


def clip(s, n):
    s = s.replace("\r", "")
    return s if len(s) <= n else s[: n // 2] + f"\n  [...{len(s) - n} chars...]\n" + s[-n // 2:]


for run in sorted(root.glob("run-0*")):
    traj = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    lines = []
    for s in traj.get("steps", []):
        sid = s.get("step_id")
        for tc in s.get("tool_calls") or []:
            args = tc.get("arguments") or {}
            cmd = args.get("keystrokes") or args.get("command") or json.dumps(args)
            lines.append(f"### step {sid} CMD:\n{clip(str(cmd), 1600)}")
        obs = s.get("observation") or {}
        for r in obs.get("results") or []:
            c = r.get("content")
            if isinstance(c, list):
                c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
            if c:
                lines.append(f"--- step {sid} OUT:\n{clip(str(c), 900)}")
        if s.get("source") == "agent" and not s.get("tool_calls") and s.get("message"):
            lines.append(f"### step {sid} MSG:\n{clip(str(s['message']), 600)}")
    (out / f"{run.name}.txt").write_text("\n".join(lines), encoding="utf-8")
    print(run.name, len(lines), "entries")
