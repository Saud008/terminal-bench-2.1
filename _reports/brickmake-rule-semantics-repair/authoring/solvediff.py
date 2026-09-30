"""Print a unified diff between each file solve.sh writes and the shipped environment copy."""

import difflib
import pathlib
import re
import sys

task = pathlib.Path(sys.argv[1])
s = (task / "solution" / "solve.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
for m in re.finditer(r"cat > (\S+) <<'(\w+)'\n(.*?)\n\2\n", s, re.S):
    path, body = m.group(1), m.group(3) + "\n"
    cur = (task / "environment" / "app" / path).read_text(encoding="utf-8").replace("\r\n", "\n")
    d = difflib.unified_diff(cur.splitlines(), body.splitlines(), "env/" + path, "fix/" + path, lineterm="", n=2)
    print("\n".join(d))
    print()
