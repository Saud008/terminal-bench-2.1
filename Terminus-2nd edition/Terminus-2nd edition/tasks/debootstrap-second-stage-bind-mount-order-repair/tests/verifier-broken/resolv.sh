#!/usr/bin/env bash
# Broken: always writes etc/resolv.conf even for merged /usr layouts.

s2_seed_resolv() {
  local rootfs="$1"
  python3 - "$rootfs" <<'PY'
import pathlib
import shutil
import sys

rootfs = pathlib.Path(sys.argv[1])
dest = rootfs / "tree" / "etc" / "resolv.conf"
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile("/app/fixtures/shared/resolv.conf.seed", dest)
print(dest)
PY
}
