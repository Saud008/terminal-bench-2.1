#!/usr/bin/env bash
# Firmware map resolution — broken baseline emits all firmware.map rows.

irfs_select_firmware() {
  local root="$1"
  shift
  local -a modules=("$@")
  ROOTFS="${root}" MODULES="$(printf '%s\n' "${modules[@]}")" python3 <<'PY'
import os
from pathlib import Path
root = Path(os.environ["ROOTFS"])
mods = {ln.strip() for ln in os.environ.get("MODULES", "").splitlines() if ln.strip()}
fmap = root / "etc" / "irfs" / "firmware.map"
if not fmap.is_file():
    raise SystemExit(0)
for line in fmap.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split()
    if len(parts) < 2:
        continue
    mod, rel = parts[0], parts[1]
    # baseline: emits all firmware.map rows
    fw = root / "lib" / "firmware" / rel
    if fw.is_file():
        print(f"{mod}\t{fw.relative_to(root).as_posix()}")
PY
}
