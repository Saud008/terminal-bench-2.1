# Oracle solve — task identity weather-radar-tilt-volume-stitcher token wradst8c
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd /app/environment

install -D -m 0644 "$ROOT_DIR/files/tilt_rank.rs" src/ken_io/latch.rs
install -D -m 0644 "$ROOT_DIR/files/azimuth_bridge.rs" src/hopf_weave/weave.rs
install -D -m 0644 "$ROOT_DIR/files/offset_apply.rs" src/m2_table/p4s.rs
install -D -m 0644 "$ROOT_DIR/files/gate_filter.rs" src/stamp_z9/v7g.rs
install -D -m 0644 "$ROOT_DIR/files/completeness.rs" src/ruelle_ratio/c6f.rs

python3 <<'PY'
from pathlib import Path

lane = Path("src/relay_lane/n3w.rs")
text = lane.read_text()
old = '''    for tilt in &bundle.tilt_scans {
        for ray in &tilt.rays {
            let bridged = weave::unified_azimuth_centideg(ray.azimuth_centideg);'''
new = '''    for tilt in &bundle.tilt_scans {
        let mut prev_raw: Option<u32> = None;
        for ray in &tilt.rays {
            let bridged = weave::unified_azimuth_centideg(ray.azimuth_centideg, prev_raw);
            prev_raw = Some(ray.azimuth_centideg);'''
if old not in text:
    raise SystemExit("lane patch anchor missing")
lane.write_text(text.replace(old, new))

emit = Path("src/peskin_emit/e5r.rs")
text = emit.read_text()
text = text.replace(
    "let azimuths: Vec<u32> = rows.iter().map(|r| r.azimuth_centideg).collect();",
    "let bridged: Vec<u32> = rows.iter().map(|r| r.bridged_azimuth_centideg).collect();",
)
text = text.replace(
    "weave::azimuth_span_centideg(&azimuths)",
    "weave::azimuth_span_centideg(&bridged)",
)
emit.write_text(text)
PY

cargo fmt --all 2>/dev/null || true
cargo build --release
test -x target/release/vrstctl
install -m 0755 target/release/vrstctl /app/bin/vrstctl

mkdir -p /app/output /app/var
bash /app/scripts/reset-var.sh
/app/bin/vrstctl stitch --bundle dual-tilt-basic --token oracle-smoke --dest /app/output/oracle-smoke.json
test -s /app/var/gate-buffer-oracle-smoke.ndjson
test -s /app/output/oracle-smoke.json

python3 - <<'PY'
import json
from pathlib import Path

body = json.loads(Path("/app/output/oracle-smoke.json").read_text())
assert body["run_token"] == "oracle-smoke"
assert body["tilt_count"] == 2
assert body["station_id"] == "KMUX"
assert body["valid_gate_total"] >= 1
assert body["coverage_fraction"] > 0.0
assert body["report_digest"]
hdr = json.loads(Path("/app/var/gate-buffer-oracle-smoke.meta.json").read_text())
assert hdr["run_token"] == "oracle-smoke"
assert hdr["row_count"] == body["valid_gate_total"] or hdr["row_count"] >= 1
assert "ledger_fingerprint" in hdr
lines = Path("/app/var/gate-buffer-oracle-smoke.ndjson").read_text().strip().splitlines()
assert len(lines) == hdr["row_count"]
for line in lines:
    row = json.loads(line)
    assert "calibrated_dbz" in row
    assert "included" in row
PY
