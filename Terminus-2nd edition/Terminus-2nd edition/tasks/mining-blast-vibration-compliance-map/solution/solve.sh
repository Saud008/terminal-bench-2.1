#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/mbvcm_r02/attenuate.rs <<'EOF'
pub fn attenuate(source_ppv: f64, distance_m: f64, reference_m: f64, exponent: f64) -> f64 {
    if distance_m <= 0.0 {
        return source_ppv;
    }
    source_ppv * (reference_m / distance_m).powf(exponent)
}
EOF

cat > /app/mbvcm_r03/apply.rs <<'EOF'
pub fn apply_calibration(raw_ppv: f64, zero_offset: f64, gain: f64) -> f64 {
    (raw_ppv - zero_offset) * gain
}
EOF

cat > /app/mbvcm_r04/mbvcm_anchor.rs <<'EOF'
use crate::types::PropertyParcel;

pub fn compliance_distance(
    blast_e: f64,
    blast_n: f64,
    parcel: &PropertyParcel,
    _sensor_e: f64,
    _sensor_n: f64,
) -> f64 {
    let mut best = f64::MAX;
    for v in &parcel.boundary_vertices {
        let dx = blast_e - v[0];
        let dy = blast_n - v[1];
        let d = (dx * dx + dy * dy).sqrt();
        if d < best {
            best = d;
        }
    }
    best
}
EOF

cat > /app/mbvcm_r05/limit.rs <<'EOF'
use crate::limit_scale;
use crate::types::LimitTable;

fn local_hour(fired_at: &str, tz_hours: i32) -> i32 {
    let hour: i32 = fired_at[11..13].parse().unwrap_or(0);
    (hour + tz_hours).rem_euclid(24)
}

pub fn pick_threshold(structure_class: &str, fired_at: &str, limits: &LimitTable, tz_hours: i32) -> f64 {
    let pair = match structure_class {
        "industrial" => &limits.industrial,
        _ => &limits.residential,
    };
    let h = local_hour(fired_at, tz_hours);
    let base = if (7..=18).contains(&h) { pair.day_mm_s } else { pair.night_mm_s };
    base * limit_scale()
}
EOF

python3 <<'PY'
from pathlib import Path
path = Path("/app/mbvcm_r06/persist.rs")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "let correlate_seq = prev.map(|b| b.correlate_seq).unwrap_or(0);",
    "let correlate_seq = prev.map(|b| b.correlate_seq).unwrap_or(0) + 1;",
)
path.write_text(text, encoding="utf-8")
PY

python3 <<'PY'
from pathlib import Path
path = Path("/app/mbvcm_r08/publish.rs")
text = path.read_text(encoding="utf-8")
text = text.replace("corrected.min(attenuated)", "corrected.max(attenuated)")
text = text.replace(
    "rows.sort_by(|a, b| a.blast_id.cmp(&b.blast_id));",
    "rows.sort_by(|a, b| {\n        (a.property_id.as_str(), a.blast_id.as_str(), a.sensor_id.as_str())\n            .cmp(&(b.property_id.as_str(), b.blast_id.as_str(), b.sensor_id.as_str()))\n    });",
)
text = text.replace(
    "atlas.atlas_digest = atlas_digest(&atlas.summary);",
    "atlas.atlas_digest = atlas_digest(&atlas.summary, &atlas.exceedance_rows);",
)
old_fn = "fn atlas_digest(summary: &ExceedanceSummary) -> String {"
if old_fn in text and "fn atlas_digest(summary: &ExceedanceSummary, rows: &[ExceedanceRow])" not in text:
    start = text.index(old_fn)
    end = text.index("}\n\npub fn write_atlas", start) + 1
    new_fn = '''fn atlas_digest(summary: &ExceedanceSummary, rows: &[ExceedanceRow]) -> String {
    use std::collections::BTreeMap;
    let mut values: Vec<f64> = rows
        .iter()
        .map(|r| (r.exceedance_mm_s * 10000.0).round() / 10000.0)
        .collect();
    values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mut obj: BTreeMap<&str, serde_json::Value> = BTreeMap::new();
    obj.insert("exceedance_count", serde_json::json!(summary.exceedance_count));
    obj.insert("exceedance_values", serde_json::json!(values));
    obj.insert("max_exceedance_mm_s", serde_json::json!(summary.max_exceedance_mm_s));
    obj.insert("reading_pairs", serde_json::json!(summary.reading_pairs));
    let body = serde_json::to_string(&obj).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}'''
    text = text[:start] + new_fn + text[end:]
path.write_text(text, encoding="utf-8")
PY

bash /app/scripts/clear-seismo-run.sh
/usr/local/cargo/bin/cargo build --release --locked --manifest-path /app/Cargo.toml
cp /app/target/release/seismocomply /app/bin/seismocomply
echo "mining-blast-vibration-compliance-map oracle ready"
