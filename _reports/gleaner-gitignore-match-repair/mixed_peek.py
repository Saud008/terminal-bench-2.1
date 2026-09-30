import json
from pathlib import Path

T = Path(__file__).resolve().parents[2] / "gleaner-gitignore-match-repair/gleaner-gitignore-match-repair/tests/cases.json"
g = json.loads(T.read_text(encoding="utf-8"))["groups"]["mixed_trees"]
for c in g:
    if c["name"] in {"mixed_00", "mixed_08", "mixed_18", "mixed_20"}:
        pats = []
        for rel, text in list(c["files"].items()) + list(c.get("home", {}).items()) + list(c.get("xdg", {}).items()):
            if rel.endswith("ignore"):
                pats += [f"{rel}: {ln!r}" for ln in text.splitlines() if "**" in ln]
        if "exclude" in c:
            pats += [f"exclude: {ln!r}" for ln in c["exclude"].splitlines() if "**" in ln]
        print(c["name"], pats)
