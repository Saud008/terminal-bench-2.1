#!/usr/bin/env bash
# Export plan JSON with staging digest validation and run-seq persistence.

export_plan_emit() {
  local output_path="$1"
  local manifest_dir="$2"
  local manifest_file="$3"
  local config_path="$4"
  local mod_count="$5"
  local edge_count="$6"
  local exit_code="$7"

  local staging_path="/app/state/parsed-manifest.tsv"
  local meta_path="/app/state/staging-meta.json"
  local run_seq_path="/app/state/run-seq.json"

  if [[ ! -f "${staging_path}" || ! -f "${meta_path}" ]]; then
    echo "export_plan: missing staging artifacts" >&2
    return 1
  fi

  local on_disk digest stored_digest
  on_disk="$(sha256sum "${staging_path}" | awk '{print $1}')"
  stored_digest="$(python3 - "${meta_path}" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1], encoding="utf-8"))["parsed_sha256"])
PY
)"
  if [[ "${on_disk}" != "${stored_digest}" ]]; then
    echo "export_plan: staging digest mismatch" >&2
    return 1
  fi

  local input_fingerprint run_seq
  read -r input_fingerprint run_seq < <(
    python3 - "${manifest_file}" "${config_path}" "${run_seq_path}" "${exit_code}" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest_file = Path(sys.argv[1])
config_path = Path(sys.argv[2])
run_seq_path = Path(sys.argv[3])
exit_code = int(sys.argv[4])

cfg = json.loads(config_path.read_text(encoding="utf-8"))
cfg_blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
fingerprint = hashlib.sha256(manifest_file.read_bytes() + b"\n" + cfg_blob).hexdigest()

run_seq = 1
stored_fp = ""
if run_seq_path.is_file():
    data = json.loads(run_seq_path.read_text(encoding="utf-8"))
    run_seq = int(data.get("seq", 1))
    stored_fp = str(data.get("input_fingerprint", ""))

if exit_code == 0:
    if run_seq_path.is_file() and stored_fp == fingerprint:
        pass
    elif run_seq_path.is_file() and stored_fp:
        run_seq = run_seq + 1
    else:
        run_seq = 1
    run_seq_path.parent.mkdir(parents=True, exist_ok=True)
    run_seq_path.write_text(
        json.dumps({"seq": run_seq, "input_fingerprint": fingerprint}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

print(fingerprint, run_seq)
PY
  )

  mkdir -p "$(dirname "${output_path}")"

  export PLAN_MANIFEST_DIR="${manifest_dir}"
  export PLAN_MOD_COUNT="${mod_count}"
  export PLAN_EDGE_COUNT="${edge_count}"
  export PLAN_RUN_SEQ="${run_seq}"
  export PLAN_MOUNT_JSON="$(printf '%s\n' "${TOPO_ORDER[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"
  export PLAN_ERRORS_JSON="$(printf '%s\n' "${DEPS_ERRORS[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"
  export PLAN_CYCLES_JSON="$(printf '%s\n' "${TOPO_CYCLES[@]-}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"

  python3 - "${output_path}" <<'PY'
import json
import os
import sys

doc = {
    "plan_version": 1,
    "manifest_dir": os.environ["PLAN_MANIFEST_DIR"],
    "mount_order": json.loads(os.environ["PLAN_MOUNT_JSON"]),
    "errors": json.loads(os.environ["PLAN_ERRORS_JSON"]),
    "cycles": json.loads(os.environ["PLAN_CYCLES_JSON"]),
    "stats": {
        "mod_count": int(os.environ["PLAN_MOD_COUNT"]),
        "edge_count": int(os.environ["PLAN_EDGE_COUNT"]),
    },
    "footer": {"run_seq": int(os.environ["PLAN_RUN_SEQ"])},
}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}
