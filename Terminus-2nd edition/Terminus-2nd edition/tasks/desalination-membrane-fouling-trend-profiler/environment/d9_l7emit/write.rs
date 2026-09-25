// export stage: publish fouling trend chronicle JSON
use crate::types::{
    ChronicleRow, ChronicleSummary, FoulingTrendChronicle, MembraneBatch, NdpGridRow, TrendScratch,
};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn element_fp(batch_id: &str, hour: u32, salinity: f64, pressure: f64) -> String {
    let body = format!("{batch_id}:{hour}:{salinity:.3}:{pressure:.3}");
    hex::encode(Sha256::digest(body.as_bytes()))[..16].to_string()
}

pub fn batch_lineage_digest(batches: &[MembraneBatch]) -> String {
    let body = batches
        .iter()
        .map(|b| format!("{}:{}", b.batch_id, b.parent_batch_id.clone().unwrap_or_default()))
        .collect::<Vec<_>>()
        .join("|");
    hex::encode(Sha256::digest(body.as_bytes()))
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
    rows.sort_by_key(|r| r.hour_index);
    let summary = ChronicleSummary {
        total_readings: rows.len() as u32,
        critical_count: rows.iter().filter(|r| r.trend_class == "critical").count() as u32,
        accelerating_count: rows.iter().filter(|r| r.trend_class == "accelerating").count() as u32,
        stable_count: rows.iter().filter(|r| r.trend_class == "stable").count() as u32,
        max_ndp: rows.iter().map(|r| r.ndp).fold(0.0_f64, f64::max),
    };
    let lin = batch_lineage_digest(batches);
    let digest = chronicle_digest(&summary);
    FoulingTrendChronicle {
        run_id: run_id.to_string(),
        train_id: train_id.to_string(),
        chronicle_rows: rows,
        summary,
        batch_lineage_digest: lin,
        chronicle_digest: digest,
    }
}

fn chronicle_digest(summary: &ChronicleSummary) -> String {
    let body = serde_json::json!({
        "accelerating_count": summary.accelerating_count,
        "critical_count": summary.critical_count,
        "max_ndp": summary.max_ndp,
        "stable_count": summary.stable_count,
        "total_readings": summary.total_readings,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}
