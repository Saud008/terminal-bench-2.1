#!/usr/bin/env bash

read_registry_record() {
  local batch="$1"
  local job_id="$2"
  local path="${REGISTRY_DIR}/${batch}.${job_id}.record.json"
  if [[ ! -f "$path" ]]; then
    echo "{}"
    return 0
  fi
  cat "$path"
}

registry_delete_record() {
  local batch="$1"
  local job_id="$2"
  local jkey="$3"
  local epoch="$4"
  rm -f "${REGISTRY_DIR}/${batch}.${job_id}.record.json"
  append_timeline "registry_delete" "$jkey" "$epoch"
}

registry_write_record() {
  local batch="$1"
  local job_id="$2"
  local epoch="$3"
  local meta_json="$4"
  local path="${REGISTRY_DIR}/${batch}.${job_id}.record.json"
  python3 - "$path" "$epoch" "$meta_json" <<'PY'
import json, sys
from pathlib import Path
path, epoch, meta = sys.argv[1:4]
doc = {"completed_at": int(epoch), "dispatch_meta": json.loads(meta), "flushed": True}
Path(path).parent.mkdir(parents=True, exist_ok=True)
Path(path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
