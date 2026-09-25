#!/usr/bin/env bash
# Staging ledger — seal binds manifest to input bytes before export.

KH_LEDGER_ROOT="${KH_LEDGER_ROOT:-/app/state}"
KH_LEDGER_FILE="${KH_LEDGER_ROOT}/kh-ledger.jsonl"
KH_MANIFEST_FILE="${KH_LEDGER_ROOT}/kh-manifest.json"

kh_ledger_reset() {
  mkdir -p "${KH_LEDGER_ROOT}"
  : > "${KH_LEDGER_FILE}"
  rm -f "${KH_MANIFEST_FILE}"
}

kh_ledger_append() {
  local rec="$1"
  [[ -n "$rec" ]] || return 0
  REC="${rec}" python3 - "${KH_LEDGER_FILE}" <<'PY'
import json, os, sys
from pathlib import Path
path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
seq = len(lines) + 1
lines.append(json.dumps({"seq": seq, "record": os.environ["REC"]}, separators=(",", ":")))
path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
PY
}

kh_ledger_seal() {
  local input_path="$1"
  LEDGER="${KH_LEDGER_FILE}" MANIFEST="${KH_MANIFEST_FILE}" INPUT="${input_path}" python3 <<'PY'
import hashlib, json, os
from pathlib import Path
ledger = Path(os.environ["LEDGER"])
manifest = Path(os.environ["MANIFEST"])
input_path = Path(os.environ["INPUT"])
ledger_bytes = ledger.read_bytes() if ledger.exists() else b""
lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
body = {
    "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
    "record_count": len(lines),
    "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
}
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(body, separators=(",", ":")) + "\n", encoding="utf-8")
PY
}

kh_ledger_verify() {
  LEDGER="${KH_LEDGER_FILE}" MANIFEST="${KH_MANIFEST_FILE}" INPUT_PATH="${KH_VERIFY_INPUT:-}" python3 <<'PY'
import hashlib, json, os, sys
from pathlib import Path
ledger = Path(os.environ["LEDGER"])
manifest = Path(os.environ["MANIFEST"])
input_path = os.environ.get("INPUT_PATH", "")
if not manifest.exists():
    sys.exit(1)
body = json.loads(manifest.read_text(encoding="utf-8"))
ledger_bytes = ledger.read_bytes() if ledger.exists() else b""
lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
if body.get("record_count") != len(lines):
    sys.exit(1)
if body.get("ledger_sha256") != hashlib.sha256(ledger_bytes).hexdigest():
    sys.exit(1)
if input_path:
    digest = hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
    if body.get("input_sha256") != digest:
        sys.exit(1)
PY
}

kh_ledger_read_records() {
  python3 - "${KH_LEDGER_FILE}" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(0)
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    print(obj["record"])
PY
}
