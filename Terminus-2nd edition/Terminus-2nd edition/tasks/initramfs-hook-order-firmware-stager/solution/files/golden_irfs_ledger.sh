#!/usr/bin/env bash
# Staging ledger — oracle JSONL seq and verification.

IRFS_LEDGER_ROOT="${IRFS_LEDGER_ROOT:-/app/state}"
IRFS_LEDGER_FILE="${IRFS_LEDGER_ROOT}/irfs-ledger.jsonl"
IRFS_MANIFEST_FILE="${IRFS_LEDGER_ROOT}/irfs-manifest.json"

irfs_ledger_reset() {
  mkdir -p "${IRFS_LEDGER_ROOT}"
  : > "${IRFS_LEDGER_FILE}"
  rm -f "${IRFS_MANIFEST_FILE}"
}

irfs_ledger_append() {
  local kind="$1"
  local name="$2"
  local path="$3"
  local hook_rank="$4"
  KIND="${kind}" NAME="${name}" PATH_REL="${path}" RANK="${hook_rank}" \
    LEDGER="${IRFS_LEDGER_FILE}" python3 <<'PY'
import json, os
from pathlib import Path
path = Path(os.environ["LEDGER"])
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
seq = len([ln for ln in lines if ln.strip()]) + 1
row = {
    "seq": seq,
    "kind": os.environ["KIND"],
    "name": os.environ["NAME"],
    "path": os.environ["PATH_REL"],
    "hook_rank": int(os.environ["RANK"]),
}
lines.append(json.dumps(row, separators=(",", ":")))
path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
PY
}

irfs_ledger_seal() {
  local root="$1"
  shift
  local -a hook_names=("$@")
  LEDGER="${IRFS_LEDGER_FILE}" MANIFEST="${IRFS_MANIFEST_FILE}" ROOT="${root}" \
    HOOKS="$(printf '%s\n' "${hook_names[@]}")" python3 <<'PY'
import hashlib, json, os
from pathlib import Path
ledger = Path(os.environ["LEDGER"])
manifest = Path(os.environ["MANIFEST"])
root = Path(os.environ["ROOT"])
ledger_bytes = ledger.read_bytes() if ledger.exists() else b""
lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
hook_order = [ln for ln in os.environ.get("HOOKS", "").splitlines() if ln.strip()]
h = hashlib.sha256()
for f in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
    rel = f.relative_to(root).as_posix()
    h.update(rel.encode("utf-8"))
    h.update(f.read_bytes())
body = {
    "rootfs_sha256": h.hexdigest(),
    "entry_count": len(lines),
    "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
    "hook_order": hook_order,
}
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(body, separators=(",", ":")) + "\n", encoding="utf-8")
PY
}

irfs_ledger_verify() {
  LEDGER="${IRFS_LEDGER_FILE}" MANIFEST="${IRFS_MANIFEST_FILE}" ROOT="${IRFS_VERIFY_ROOTFS:-}" python3 <<'PY'
import hashlib, json, os, sys
from pathlib import Path
ledger = Path(os.environ["LEDGER"])
manifest = Path(os.environ["MANIFEST"])
root = os.environ.get("ROOT", "")
if not manifest.exists():
    sys.exit(1)
body = json.loads(manifest.read_text(encoding="utf-8"))
ledger_bytes = ledger.read_bytes() if ledger.exists() else b""
lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
if body.get("entry_count") != len(lines):
    sys.exit(1)
if body.get("ledger_sha256") != hashlib.sha256(ledger_bytes).hexdigest():
    sys.exit(1)
if root:
    rootp = Path(root)
    h = hashlib.sha256()
    for f in sorted((p for p in rootp.rglob("*") if p.is_file()), key=lambda p: p.relative_to(rootp).as_posix()):
        rel = f.relative_to(rootp).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(f.read_bytes())
    if body.get("rootfs_sha256") != h.hexdigest():
        sys.exit(1)
PY
}

irfs_ledger_count() {
  if [[ -f "${IRFS_LEDGER_FILE}" ]]; then
    python3 - "${IRFS_LEDGER_FILE}" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
print(len([ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]))
PY
  else
    echo 0
  fi
}
