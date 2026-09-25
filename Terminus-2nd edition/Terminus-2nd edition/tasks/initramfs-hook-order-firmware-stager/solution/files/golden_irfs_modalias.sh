#!/usr/bin/env bash
# Modalias selection — oracle glob matching.

irfs_select_modules() {
  local root="$1"
  local kver="$2"
  ROOTFS="${root}" KVER="${kver}" python3 <<'PY'
import fnmatch, os
from pathlib import Path
root = Path(os.environ["ROOTFS"])
kver = os.environ["KVER"]

def lines(p):
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8-sig")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]

requested = lines(root / "etc" / "irfs" / "modules.load")
pci_ids = lines(root / "etc" / "irfs" / "pci.ids")
alias_path = root / "lib" / "modules" / kver / "modules.alias"
aliases = []
if alias_path.is_file():
    for line in alias_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "alias":
            aliases.append((parts[1], parts[2]))
for mod in requested:
    for pattern, modname in aliases:
        if modname != mod:
            continue
        if any(fnmatch.fnmatchcase(pci, pattern) for pci in pci_ids):
            print(mod)
            break
PY
}
