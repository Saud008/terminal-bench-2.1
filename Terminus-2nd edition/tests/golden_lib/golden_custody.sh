#!/usr/bin/env bash

init_custody_journal() {
  mkdir -p "$(dirname "${CUSTODY_JOURNAL_PATH}")"
  : > "${CUSTODY_JOURNAL_PATH}"
}

append_custody_receipt() {
  local qid="$1"
  local qclass="$2"
  local seed="$3"
  local seq="$4"
  python3 - "$qid" "$qclass" "$seed" "$seq" "${CUSTODY_JOURNAL_PATH}" <<'PY'
import hashlib, json, sys
qid, qclass, seed, seq_s, path = sys.argv[1:6]
seq = int(seq_s)
if qclass == "virus":
    payload = f"{qid}|{seed}|{seq}|{qclass}"
else:
    payload = f"{seed}|{qid}|{seq}|{qclass}"
receipt = hashlib.sha256(payload.encode()).hexdigest()[:16]
row = {
    "sequence": seq,
    "quarantine_id": qid,
    "class": qclass,
    "receipt": receipt,
}
with open(path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
PY
}

compute_custody_root() {
  CUSTODY_ROOT="$(python3 - "${CUSTODY_JOURNAL_PATH}" <<'PY'
import hashlib, json, sys
from pathlib import Path
path = Path(sys.argv[1])
receipts = []
if path.is_file():
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        receipts.append(json.loads(line)["receipt"])
if receipts:
    print(hashlib.sha256("\n".join(receipts).encode()).hexdigest(), end="")
else:
    print("", end="")
PY
)"
}

write_prepare_seal() {
  local scenario_label="$1"
  local seed="$2"
  local requests_path="$3"
  python3 - "$scenario_label" "$seed" "$requests_path" "${SEAL_PATH}" "${STAGING_PATH}" <<'PY'
import hashlib, json, sys
from pathlib import Path

scenario, seed, requests_path, seal_path, staging_path = sys.argv[1:6]
policy_digest = ""
release_epoch = 0
if Path(staging_path).is_file():
    staging = json.loads(Path(staging_path).read_text(encoding="utf-8"))
    policy_digest = staging.get("policy_digest", "") or ""
    release_epoch = int(staging.get("release_epoch", 0) or 0)
fingerprint = hashlib.sha256(f"{scenario}:{seed}:{policy_digest}".encode()).hexdigest()[:24]
seal = {
    "scenario": scenario,
    "seed": seed,
    "requests_path": requests_path,
    "release_epoch": release_epoch,
    "policy_digest": policy_digest,
    "prepare_fingerprint": fingerprint,
}
Path(seal_path).write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if Path(staging_path).is_file():
    staging = json.loads(Path(staging_path).read_text(encoding="utf-8"))
    staging["prepare_fingerprint"] = fingerprint
    Path(staging_path).write_text(json.dumps(staging, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

read_prepare_seal() {
  SEAL_SCENARIO=""
  SEAL_SEED=""
  SEAL_REQUESTS=""
  SEAL_FINGERPRINT=""
  local parsed
  parsed="$(python3 - "${SEAL_PATH}" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(1)
doc = json.loads(path.read_text(encoding="utf-8"))
for key in ("scenario", "seed", "requests_path", "prepare_fingerprint"):
    if key not in doc or doc[key] in (None, ""):
        raise SystemExit(1)
print(doc["scenario"])
print(doc["seed"])
print(doc["requests_path"])
print(doc["prepare_fingerprint"])
PY
)" || return 1
  SEAL_SCENARIO="$(printf '%s\n' "$parsed" | sed -n '1p')"
  SEAL_SEED="$(printf '%s\n' "$parsed" | sed -n '2p')"
  SEAL_REQUESTS="$(printf '%s\n' "$parsed" | sed -n '3p')"
  SEAL_FINGERPRINT="$(printf '%s\n' "$parsed" | sed -n '4p')"
  [[ -n "$SEAL_SCENARIO" && -n "$SEAL_SEED" && -n "$SEAL_REQUESTS" ]]
}
