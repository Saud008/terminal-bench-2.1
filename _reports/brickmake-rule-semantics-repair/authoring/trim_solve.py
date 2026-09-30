"""Keep only the heredoc blocks of solve.sh that write the given files."""

import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
keep = set(sys.argv[2:])
s = path.read_text(encoding="utf-8")
head, _, _ = s.partition("cat > ")
blocks = re.findall(r"(cat > (\S+) <<'(\w+)'\n.*?\n\3\n)", s, re.S)
tail = s[s.rfind("\n" + blocks[-1][2] + "\n") + len(blocks[-1][2]) + 2:]
body = "\n".join(b for b, name, _ in blocks if name in keep)
path.write_text(head + body + tail, encoding="utf-8", newline="\n")
print("kept", [name for _, name, _ in blocks if name in keep])
