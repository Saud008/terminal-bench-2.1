#!/usr/bin/env bash
set -euo pipefail
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

sed -i 's/(temperature \/ t_ref)/(t_ref \/ temperature)/' /app/d9_p3norm/normalize.rs
sed -i 's/salinity_ppt + cal_offset_ppt/salinity_ppt - cal_offset_ppt/' /app/d9_c5anchor/anchor.rs
sed -i 's/hour > e.hour_index/hour == e.hour_index/' /app/d9_c5anchor/anchor.rs
sed -i 's/hour > b.active_from_hour && hour < b.active_until_hour/hour >= b.active_from_hour \&\& hour <= b.active_until_hour/' /app/d9_m2lineage/map.rs
sed -i 's/ (n as f64);/ (n as f64 - 1.0);/' /app/d9_s6trend/score.rs

cat > /app/d9_g4bridge/bridge.rs <<'EOF'
use crate::types::ReadingRow;

pub fn bridge_readings(rows: &[ReadingRow]) -> Vec<ReadingRow> {
    let mut sorted = rows.to_vec();
    sorted.sort_by_key(|r| r.hour_index);
    let mut out = Vec::new();
    for (idx, row) in sorted.iter().enumerate() {
        let mut r = row.clone();
        if row.sensor_flags.contains("salinity_dropout") {
            if let Some(prev) = sorted.get(idx.saturating_sub(1)) {
                r.salinity_ppt = prev.salinity_ppt;
            }
        }
        if row.sensor_flags.contains("pressure_dropout") {
            if let (Some(a), Some(b)) = (sorted.get(idx.saturating_sub(1)), sorted.get(idx + 1)) {
                let span = (b.hour_index - a.hour_index) as f64;
                let frac = (row.hour_index - a.hour_index) as f64 / span;
                r.pressure_bar = a.pressure_bar + frac * (b.pressure_bar - a.pressure_bar);
            }
        }
        if row.sensor_flags.contains("flow_dropout") {
            if let (Some(a), Some(b)) = (sorted.get(idx.saturating_sub(1)), sorted.get(idx + 1)) {
                let span = (b.hour_index - a.hour_index) as f64;
                let frac = (row.hour_index - a.hour_index) as f64 / span;
                r.flow_m3h = a.flow_m3h + frac * (b.flow_m3h - a.flow_m3h);
            }
        }
        out.push(r);
    }
    out
}
EOF

cat > /app/d9_l7emit/write.rs <<'EOF'
use crate::types::{
    ChronicleRow, ChronicleSummary, FoulingTrendChronicle, MembraneBatch, NdpGridRow, TrendScratch,
};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn element_fp(batch_id: &str, hour: u32, salinity: f64, pressure: f64) -> String {
    let body = format!("{batch_id}:{hour}:{salinity:.3}:{pressure:.3}");
    hex::encode(Sha256::digest(body.as_bytes()))[..16].to_string()
}

fn severity_rank(trend: &str) -> u8 {
    match trend {
        "critical" => 0,
        "accelerating" => 1,
        _ => 2,
    }
}

pub fn batch_lineage_digest(batches: &[MembraneBatch]) -> String {
    let mut pairs: Vec<String> = batches
        .iter()
        .map(|b| format!("{}:{}", b.batch_id, b.parent_batch_id.clone().unwrap_or_default()))
        .collect();
    pairs.sort();
    hex::encode(Sha256::digest(pairs.join("|").as_bytes()))
}

pub fn build_chronicle(
    run_id: &str,
    train_id: &str,
    scratch: &TrendScratch,
    grid: &[NdpGridRow],
    batches: &[MembraneBatch],
) -> FoulingTrendChronicle {
    let grid_map: BTreeMap<u32, &NdpGridRow> = grid.iter().map(|g| (g.hour_index, g)).collect();
    let mut rows = Vec::new();
    for tr in &scratch.rows {
        let sal = grid_map.get(&tr.hour_index).map(|g| g.salinity_ppt).unwrap_or(0.0);
        let pres = grid_map.get(&tr.hour_index).map(|g| g.pressure_bar).unwrap_or(0.0);
        rows.push(ChronicleRow {
            hour_index: tr.hour_index,
            batch_id: tr.batch_id.clone(),
            ndp: tr.ndp,
            trend_class: tr.trend_class.clone(),
            element_fp: element_fp(&tr.batch_id, tr.hour_index, sal, pres),
        });
    }
    rows.sort_by(|a, b| {
        severity_rank(&a.trend_class)
            .cmp(&severity_rank(&b.trend_class))
            .then(a.hour_index.cmp(&b.hour_index))
    });
    let summary = ChronicleSummary {
        total_readings: rows.len() as u32,
        critical_count: rows.iter().filter(|r| r.trend_class == "critical").count() as u32,
        accelerating_count: rows.iter().filter(|r| r.trend_class == "accelerating").count() as u32,
        stable_count: rows.iter().filter(|r| r.trend_class == "stable").count() as u32,
        max_ndp: rows.iter().map(|r| r.ndp).fold(0.0_f64, f64::max),
    };
    let lin = batch_lineage_digest(batches);
    let digest = chronicle_digest(&summary, &rows);
    FoulingTrendChronicle {
        run_id: run_id.to_string(),
        train_id: train_id.to_string(),
        chronicle_rows: rows,
        summary,
        batch_lineage_digest: lin,
        chronicle_digest: digest,
    }
}

fn chronicle_digest(summary: &ChronicleSummary, rows: &[ChronicleRow]) -> String {
    let mut values: Vec<f64> = rows.iter().map(|r| (r.ndp * 10000.0).round() / 10000.0).collect();
    values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let body = serde_json::json!({
        "accelerating_count": summary.accelerating_count,
        "critical_count": summary.critical_count,
        "max_ndp": summary.max_ndp,
        "ndp_values": values,
        "stable_count": summary.stable_count,
        "total_readings": summary.total_readings,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}
EOF

test -d "$SOL/patches" || exit 1

bash /app/scripts/reset-workspace.sh
/usr/local/cargo/bin/cargo build --release --locked --manifest-path /app/Cargo.toml
cp /app/target/release/rotrace /app/bin/rotrace
echo "desalination-membrane-fouling-trend-profiler oracle ready"
