"""Summarise a run_k job: per-trial test results and notable agent commands."""
import json
import pathlib
import re
import sys

job = pathlib.Path(sys.argv[1])
for trial in sorted(p for p in job.iterdir() if p.is_dir()):
    ctrf = trial / "verifier" / "ctrf.json"
    if not ctrf.exists():
        continue
    tests = json.loads(ctrf.read_text())["results"]["tests"]
    print(f"== {trial.name}")
    for t in tests:
        print(f"   {t['status']:7} {t['name'].split('::')[-1]}")
    traj = json.loads((trial / "agent" / "trajectory.json").read_text())
    cmds = []
    for step in traj.get("steps", []):
        for call in step.get("tool_calls", []) or []:
            args = call.get("arguments", {})
            ks = args.get("keystrokes") if isinstance(args, dict) else None
            if ks:
                cmds.append(ks.strip())
    pat = re.compile(r"apt|ssh -G|/usr/bin/ssh|openssh|git clone|curl|wget|pip")
    hits = [c for c in cmds if pat.search(c)]
    print(f"   commands={len(cmds)} network/ssh-related={len(hits)}")
    for c in hits[:12]:
        print("     $", c[:160].replace("\n", " "))
    last = traj["steps"][-1]
    msg = last.get("message") or ""
    print("   final message:", str(msg)[:600].replace("\n", " "))
