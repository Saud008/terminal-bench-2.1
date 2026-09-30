import json
import re
from pathlib import Path

R = Path(__file__).resolve().parents[2]
inner = R / "gleaner-gitignore-match-repair/gleaner-gitignore-match-repair"
src = inner / "environment/app/src"
for name in ("fn wildmatch", "fn sort_paths", "fn trim_trailing_spaces"):
    hits = [str(p.relative_to(src)) for p in src.rglob("*.rs") if name in p.read_text(encoding="utf-8")]
    print(name, hits)
g = json.loads((inner / "tests/cases.json").read_text(encoding="utf-8"))["groups"]
print("escaped no-match lines:", sum(c["check"].count("::\t") for c in g["escaped_leading_characters"]))
print("check_rc values:", sorted({c["check_rc"] for grp in g.values() for c in grp}))
print("list_order lists:", [c["list"] for c in g["list_order"]])
docs_rx = re.compile(r"(>|sed -i|tee|open\([^)]*docs[^)]*'w'|cat > )[^\n]*docs/")
for n in range(1, 6):
    text = (R / f"_reports/gleaner-gitignore-match-repair/cmdsfull/run-0{n}_cmds.txt").read_text(encoding="utf-8")
    print(f"run-0{n} docs writes:", docs_rx.findall(text), "tests/ refs:", len(re.findall(r"/tests/|/solution/|/logs/verifier", text)))
