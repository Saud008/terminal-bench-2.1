#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

run_seal() {
  local midstate="$1" bundle="$2"
  ensure_runtime_dirs
  python3 - "$midstate" "$bundle" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

REQUIRED = (
    "seed",
    "trace",
    "midstate_digest",
    "pairing_confirms",
    "resume_tokens_cleared",
    "gatt_resolve_count",
    "reconnect_attempts",
    "disconnect_reasons",
    "ledger_rows",
)


def require_fields(doc: dict) -> dict:
    for key in REQUIRED:
        if key not in doc:
            raise SystemExit(f"missing midstate field: {key}")
    return doc


def normalize_rows(rows: list) -> list:
    return list(rows)


def counts_from_midstate(doc: dict) -> dict:
    return {
        "pairing_confirms": doc["pairing_confirms"],
        "resume_tokens_cleared": doc["resume_tokens_cleared"],
        "gatt_resolve_count": doc["gatt_resolve_count"],
        "reconnect_attempts": doc["reconnect_attempts"],
    }


def seal_bundle(doc: dict) -> dict:
    rows = normalize_rows(list(doc.get("ledger_rows", [])))
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    ledger_fingerprint = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    bundle_seal = hashlib.sha256(
        f"{doc['midstate_digest']}|{ledger_fingerprint}|{doc['seed']}".encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "seed": doc["seed"],
        "trace": doc["trace"],
        "counts": counts_from_midstate(doc),
        "disconnect_reasons": doc["disconnect_reasons"],
        "ledger_fingerprint": ledger_fingerprint,
        "bundle_seal": bundle_seal,
    }


midstate_path, bundle_path = sys.argv[1:3]
doc = require_fields(json.loads(Path(midstate_path).read_text(encoding="utf-8")))
out = seal_bundle(doc)
Path(bundle_path).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
