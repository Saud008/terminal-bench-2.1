import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tb21"))
import master_check as mc  # noqa: E402

outer = ROOT / "gleaner-gitignore-match-repair"
rubric = {}
for ln in (outer / "rubric.txt").read_text(encoding="utf-8").splitlines():
    body, pts = ln.rsplit(", ", 1)
    rubric[body] = int(pts)

for run in sys.argv[1:] or [f"run-0{i}" for i in range(1, 6)]:
    d = outer / "trajectories" / run
    rs = d / "rubric_score.txt"
    if not rs.is_file():
        print(run, "no rubric_score.txt")
        continue
    parts = []
    mc.walk_strings(json.loads((d / "agent/trajectory.json").read_text(encoding="utf-8")), parts)
    for extra in ("verifier/test-stdout.txt", "agent/terminus_2.pane"):
        parts.append((d / extra).read_text(encoding="utf-8", errors="replace"))
    mc.walk_strings(json.loads((d / "verifier/ctrf.json").read_text(encoding="utf-8")), parts)
    corpus = mc.norm("\n".join(parts))
    raw = rs.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        print(run, "BOM/CR")
    rows, total = mc.parse_score(raw.decode("utf-8"))
    s = 0
    for crit, verdict, pts, ev in rows:
        if crit not in rubric:
            print(run, "UNKNOWN CRIT", crit[:60])
            continue
        want = rubric[crit] if verdict == "MET" else 0
        val = int(re.sub(r"[^-+0-9]", "", pts) or "0")
        if val != want:
            print(run, "PTS", crit[:50], pts, want)
        s += val
        for q in re.findall(r"`([^`]+)`", ev):
            if not mc.quote_in(q, corpus):
                print(run, "MISSING", q)
    if len(rows) != len(rubric):
        print(run, "rows", len(rows))
    print(run, "total", total, "recomputed", s)
