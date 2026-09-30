"""Second independent re-derivation with BIND's named-compilezone.

Include paths are rewritten to absolute paths (BIND resolves them against
its working directory). Record sets are compared as multisets of lines,
since BIND's own output order is not the canonical order.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

cases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["groups"]
root = Path("/tmp/bc")
shutil.rmtree(root, ignore_errors=True)
inc = re.compile(r"^\$INCLUDE\s+(\S+)(.*)$", re.M)
for group, lst in cases.items():
    for c in lst:
        if c["rc"] != 0:
            continue
        base = root / group / c["name"]
        for rel, text in c["files"].items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)

            def fix(m, d=p.parent):
                return f"$INCLUDE {(d / m.group(1)).as_posix()}{m.group(2)}"

            p.write_text(inc.sub(fix, text), encoding="utf-8")
        r = subprocess.run(["named-compilezone", "-q", "-i", "none", "-k", "ignore", "-n", "ignore",
                            "-s", "full", "-o", "-", c["origin"], str(base / c["entry"])],
                           capture_output=True, text=True)
        bind = []
        for line in r.stdout.splitlines():
            f = line.split(None, 4)
            if len(f) < 5:
                continue
            bind.append("\t".join([f[0].lower(), f[1], f[2], f[3], f[4]]))
        ours = c["stdout"].splitlines()
        if sorted(bind) == sorted(ours):
            print(f"ok  {group}/{c['name']}")
            continue
        print(f"--- {group}/{c['name']} (rc={r.returncode}) {r.stderr.strip()[:300]}")
        for x in sorted(set(bind) - set(ours)):
            print(f"  bind only:  {x}")
        for x in sorted(set(ours) - set(bind)):
            print(f"  zonec only: {x}")
