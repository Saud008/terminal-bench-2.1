#!/usr/bin/env bash
# Staging ledger — broken baseline writes raw lines without JSONL seq.

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
  # baseline: plain text, not JSONL with seq
  printf '%s\t%s\t%s\t%s\n' "${kind}" "${name}" "${path}" "${hook_rank}" >> "${IRFS_LEDGER_FILE}"
}

irfs_ledger_seal() {
  local root="$1"
  shift
  local -a hook_names=("$@")
  LEDGER="${IRFS_LEDGER_FILE}" MANIFEST="${IRFS_MANIFEST_FILE}" ROOT="${root}" \
    HOOKS="$(printf '%s\n' "${hook_names[@]}")" python3 <<'PY'
import hashlib, json, os, sys
from pathlib import Path
ledger = Path(os.environ["LEDGER"])
manifest = Path(os.environ["MANIFEST"])
root = Path(os.environ["ROOT"])
ledger_bytes = ledger.read_bytes() if ledger.exists() else b""
lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
hook_order = [ln for ln in os.environ.get("HOOKS", "").splitlines() if ln.strip()]
# baseline: rootfs digest uses directory name only (matches scan stub)
digest = hashlib.sha256(root.name.encode()).hexdigest()
body = {
    "rootfs_sha256": digest,
    "entry_count": len(lines),
    "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
    "hook_order": hook_order,
}
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(body, separators=(",", ":")) + "\n", encoding="utf-8")
PY
}

irfs_ledger_verify() {
  return 0
}

irfs_ledger_count() {
  if [[ -f "${IRFS_LEDGER_FILE}" ]]; then
    wc -l < "${IRFS_LEDGER_FILE}" | tr -d ' '
  else
    echo 0
  fi
}
