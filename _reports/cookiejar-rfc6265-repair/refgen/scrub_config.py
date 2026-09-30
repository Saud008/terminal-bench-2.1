"""Rewrites host paths (task path, trials_dir, trial_uri) in trajectories/run-0N/{config,result}.json to /terminal-bench2.1/<slug>."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SLUG = "cookiejar-rfc6265-repair"
CANON = f"/terminal-bench2.1/{SLUG}"
HOST = r'"(?:/mnt/c/Users/|/home/saud/)[^"]*"'

for run in sorted((ROOT / SLUG / "trajectories").glob("run-0*")):
    for name in ("config.json", "result.json"):
        p = run / name
        t = p.read_bytes().decode("utf-8")
        t2 = re.sub(r'("(?:path|trials_dir)":\s*)' + HOST, lambda m: f'{m.group(1)}"{CANON}"', t)
        t2 = re.sub(r'("trial_uri":\s*)' + HOST.replace('"(?:', '"file://(?:'), lambda m: f'{m.group(1)}"file://{CANON}"', t2)
        p.write_bytes(t2.encode("utf-8"))
        print(run.name, name, "changed" if t != t2 else "same", "left:", bool(re.search(r"/Users/|/home/saud", t2)))
