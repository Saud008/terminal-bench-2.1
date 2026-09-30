"""Run inside the reference image: records expected listings into cases.json.

usage: python3 gen_cases.py /path/to/zonec out.json
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cases_src import GROUPS  # noqa: E402

binary, out = sys.argv[1], sys.argv[2]
root = Path("/tmp/gen")
shutil.rmtree(root, ignore_errors=True)
result = {"groups": {}}
problems = []
for group, cases in GROUPS.items():
    result["groups"][group] = []
    for c in cases:
        base = root / group / c["name"]
        for rel, text in c["files"].items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        p = subprocess.run([binary, "-o", c["origin"], str(base / c["entry"])],
                           capture_output=True, text=True, cwd="/")
        entry = {k: c[k] for k in ("name", "origin", "entry", "files")}
        entry["rc"] = p.returncode
        entry["stdout"] = p.stdout
        if c["error"]:
            ef, el = c["error"]
            prefix = f"{base}/{ef}:{el}: "
            if p.returncode != 1 or p.stdout or not p.stderr.startswith(prefix):
                problems.append(f"{group}/{c['name']}: want error {prefix!r}, got rc={p.returncode} {p.stderr!r}")
            entry["error_file"], entry["error_line"] = ef, el
        else:
            if p.returncode != 0 or p.stderr:
                problems.append(f"{group}/{c['name']}: rc={p.returncode} {p.stderr!r}")
            entry["error_file"], entry["error_line"] = None, None
        result["groups"][group].append(entry)
        print(f"== {group}/{c['name']} rc={p.returncode}")
        print(p.stdout or p.stderr, end="")

Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
if problems:
    print("PROBLEMS:\n" + "\n".join(problems))
    sys.exit(1)
