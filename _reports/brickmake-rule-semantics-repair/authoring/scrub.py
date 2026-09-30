"""scrub.py <trajectories-dir> <slug>: rewrite local paths in config.json/result.json path fields only
(keys containing path/dir/uri) to /terminal-bench4.0/<slug> (check 89). Other fields are untouched."""
import json
import re
import sys
from pathlib import Path

root, slug = Path(sys.argv[1]), sys.argv[2]
pat = re.compile(r'("(?P<key>[A-Za-z_]*(?:path|dir|uri)[A-Za-z_]*)"\s*:\s*")(?P<scheme>file://)?/(?:mnt/c|Users|home/saud)/[^"]*"')
for f in sorted(root.glob("run-*/*.json")):
    text = f.read_text(encoding="utf-8")
    keys = []

    def sub(m):
        keys.append(m.group("key"))
        return f'{m.group(1)}{m.group("scheme") or ""}/terminal-bench4.0/{slug}"'

    new = pat.sub(sub, text)
    if new != text:
        json.loads(new)
        f.write_text(new, encoding="utf-8", newline="")
    print(f"{f.relative_to(root)}: {keys}")
