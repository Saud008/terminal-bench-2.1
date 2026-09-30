"""For each run, print the first step and line of agent keystrokes that hit each fix pattern."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[3] / "zonefile-master-repair" / "trajectories"
pats = {
    "origin": r"ctx->origin = origin;",
    "ttlprec": r"has_dollar",
    "restore": r"ctx->ttl = saved",
    "strrchr": r"strrchr\(including",
    "lexer": r"inq",
    "fold": r"fold|'A' && c <= 'Z'|tolower",
    "lablen": r"lablen|LABEL_MAX",
    "canon": r"name_cmp|canonical|label_cmp|name_order",
    "rrsetttl": r"first|ttl =|->ttl",
    "digestorder": r"zonemd_update",
    "apex": r"is_apex|apex",
    "serial": r"soa_serial",
    "pad": r"buflen|112",
}
for run in sorted(root.glob("run-0*")):
    traj = json.loads((run / "agent" / "trajectory.json").read_text(encoding="utf-8"))
    print("=====", run.name)
    for key, pat in pats.items():
        hits = []
        for i, s in enumerate(traj["steps"]):
            for tc in s.get("tool_calls") or []:
                k = (tc.get("arguments") or {}).get("keystrokes") or ""
                if not re.search(r"write_text|open\(p, ?'w'\)|sed -i|cat >+ ?src|replace\(", k):
                    continue
                for line in k.splitlines():
                    if re.search(pat, line):
                        hits.append(f"{i:03d}: {line.strip()[:170]}")
        print(f" [{key}]")
        for h in hits[:4]:
            print("   ", h)
