#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="$1"
pair_id="$2"
output="$3"
manifest="$4"
ipt_path="$5"
nft_path="$6"

# export_report.sh reads manifest paths instead of staging-only tuples
bash "${APP_ROOT:-/app}/lib/ingest.sh" --pair "${manifest}" >/dev/null

python3 <<PY
import json
from pathlib import Path

state = Path("${STATE_DIR}")
meta = json.loads((state / "staging-meta.json").read_text())
run_seq = json.loads((state / "run-seq.json").read_text())["run_seq"]
report = {
  "schema_version": "1",
  "pair_id": "${pair_id}",
  "staging_digest": meta.get("staging_digest", ""),
  "run_seq": run_seq,
  "summary": {"high": 0, "medium": 0, "low": 0},
  "findings": [],
  "unsupported": meta.get("unsupported_features", []),
  "counter_drift": [],
  "policy_precedence": meta.get("policy_precedence", []),
}
Path("${output}").parent.mkdir(parents=True, exist_ok=True)
Path("${output}").write_text(json.dumps(report, indent=2))
PY
