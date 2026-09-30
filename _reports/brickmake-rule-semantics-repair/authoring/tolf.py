"""Convert every text file under the given roots to LF without BOM."""

import pathlib
import sys

changed = 0
for root in sys.argv[1:]:
    for p in pathlib.Path(root).rglob("*"):
        if not p.is_file():
            continue
        b = p.read_bytes()
        if b"\0" in b[:8192]:
            continue
        nb = b.removeprefix(b"\xef\xbb\xbf").replace(b"\r\n", b"\n")
        if nb != b:
            p.write_bytes(nb)
            changed += 1
print(f"normalized {changed} file(s)")
