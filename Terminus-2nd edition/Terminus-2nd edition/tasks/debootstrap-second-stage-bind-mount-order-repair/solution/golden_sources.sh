#!/usr/bin/env bash

s2_update_apt_sources() {
  local rootfs="$1"
  local codename="$2"
  local retries="$3"
  python3 - "$rootfs" "$codename" "$retries" <<'PY'
import hashlib
import pathlib
import sys

rootfs, codename, retries = sys.argv[1:4]
retries = int(retries)
dest = pathlib.Path(rootfs) / "tree" / "etc" / "apt" / "sources.list.d" / "debian-stage2.list"
dest.parent.mkdir(parents=True, exist_ok=True)
line = f"deb http://deb.debian.org/debian {codename} main"
existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
passes = 1 + retries
for _ in range(passes):
    if line not in existing:
        with open(dest, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        existing = dest.read_text(encoding="utf-8")
print(hashlib.sha256(dest.read_bytes()).hexdigest())
PY
}
