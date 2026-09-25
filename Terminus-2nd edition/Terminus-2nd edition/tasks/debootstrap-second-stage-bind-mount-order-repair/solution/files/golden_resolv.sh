#!/usr/bin/env bash

s2_seed_resolv() {
  local rootfs="$1"
  python3 - "$rootfs" "$S2_META_MERGED_USR" <<'PY'
import pathlib
import shutil
import sys

rootfs = pathlib.Path(sys.argv[1])
merged = int(sys.argv[2]) == 1
if merged:
    dest = rootfs / "tree" / "usr" / "etc" / "resolv.conf"
else:
    dest = rootfs / "tree" / "etc" / "resolv.conf"
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile("/app/fixtures/shared/resolv.conf.seed", dest)
print(dest)
PY
}
