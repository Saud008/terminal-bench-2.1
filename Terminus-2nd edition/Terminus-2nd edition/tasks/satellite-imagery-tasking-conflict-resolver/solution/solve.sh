#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app/environment

install -D -m 0644 "$ROOT_DIR/files/wx_mode_dwell.rs" src/wx_mode_dwell.rs
install -D -m 0644 "$ROOT_DIR/files/wx_risk_blend.rs" src/wx_risk_blend.rs
install -D -m 0644 "$ROOT_DIR/files/wx_rank_gate.rs" src/wx_rank_gate.rs
install -D -m 0644 "$ROOT_DIR/files/wx_temporal_pad.rs" src/wx_temporal_pad.rs
install -D -m 0644 "$ROOT_DIR/files/wx_pair_journal.rs" src/wx_pair_journal.rs
patch -p0 src/wx_plan_seal.rs < "$ROOT_DIR/files/wx_plan_seal.patch"
install -D -m 0644 "$ROOT_DIR/files/wx_schedule_core.rs" src/wx_schedule_core.rs

cargo fmt --all 2>/dev/null || true
cargo build --release
test -x target/release/imgctl
install -m 0755 target/release/imgctl /app/bin/imgctl

mkdir -p /app/output /app/var
bash /app/scripts/purge-workspace.sh
/app/bin/imgctl resolve --scenario dual-pass-basic --token oracle-smoke --dest /app/output/oracle-smoke.json
test -s /app/var/conflict-matrix-oracle-smoke.csv
test -s /app/output/oracle-smoke.json
test -f /app/var/conflict-matrix-oracle-smoke.meta.json

python3 - <<'PY'
import json
from pathlib import Path
body = json.loads(Path("/app/output/oracle-smoke.json").read_text())
assert body["run_token"] == "oracle-smoke"
assert body["assignment_count"] == 3
assert body["plan_digest"]
assert len(body["assignments"]) == 3
hdr = json.loads(Path("/app/var/conflict-matrix-oracle-smoke.meta.json").read_text())
assert hdr["run_token"] == "oracle-smoke"
assert hdr["row_count"] == 3
assert hdr.get("matrix_fingerprint")
PY

test "$(python3 -c 'import json;print(json.load(open("/app/output/oracle-smoke.json"))["assignment_count"])')" = "3"
