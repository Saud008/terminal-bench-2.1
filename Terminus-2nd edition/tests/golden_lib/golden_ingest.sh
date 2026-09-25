#!/usr/bin/env bash

ingest_scenario() {
  local scenario_dir="$1"
  rm -rf "$SPAM_SPOOL"/* "$VIRUS_SPOOL"/* "$RELEASED_SPAM"/* "$RELEASED_VIRUS"/*
  mkdir -p "$SPAM_SPOOL" "$VIRUS_SPOOL" "$RELEASED_SPAM" "$RELEASED_VIRUS" /app/state
  shopt -s nullglob
  local f
  for f in "${scenario_dir}/spool/spam/"*; do
    [[ -e "$f" ]] && cp -a "$f" "$SPAM_SPOOL/"
  done
  for f in "${scenario_dir}/spool/virus/"*; do
    [[ -e "$f" ]] && cp -a "$f" "$VIRUS_SPOOL/"
  done
  shopt -u nullglob
  python3 - "$scenario_dir" <<'PY'
import json, sys
from pathlib import Path
scenario = Path(sys.argv[1])
rows = []
for cls in ("spam", "virus"):
    root = scenario / "spool" / cls
    if not root.is_dir():
        continue
    for meta in sorted(root.glob("msg.*.meta.json")):
        qid = meta.name.removeprefix("msg.").removesuffix(".meta.json")
        doc = json.loads(meta.read_text(encoding="utf-8"))
        rows.append({
            "quarantine_id": qid,
            "stored_class": doc.get("class", cls),
            "spool_subdir": cls,
            "bytes": int(doc.get("bytes", 0)),
        })
manifest = {"messages": sorted(rows, key=lambda r: r["quarantine_id"])}
out = Path("/app/state/spool-manifest.json")
out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
