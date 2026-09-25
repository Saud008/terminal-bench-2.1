use crate::types::{Config, DriftRow, ManifestLatch, MsgRow, SkewAtlas, SyncPair};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn audit_digest(atlas: &SkewAtlas) -> String {
    let mut topics: Vec<String> = atlas.drift_rows.iter().map(|d| d.topic.clone()).collect();
    topics.sort();
    let body = serde_json::json!({
        "bag_id": atlas.bag_id,
        "drop_count": atlas.drop_count,
        "sync_pair_count": atlas.sync_pair_count,
        "topics": topics,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

fn count_drops(rows: &[MsgRow]) -> u32 {
    let mut last_seq: BTreeMap<String, u64> = BTreeMap::new();
    let mut drops = 0u32;
    for row in rows {
        if let Some(prev) = last_seq.get(&row.topic) {
            if row.seq > *prev + 1 {
                drops += (row.seq - prev - 1) as u32;
            }
        }
        last_seq.insert(row.topic.clone(), row.seq);
    }
    drops
}

pub fn build_atlas(
    cfg: &Config,
    meta: &ManifestLatch,
    timeline_ledger_path: &str,
    sync_lattice_path: &str,
) -> Result<SkewAtlas, String> {
    let msg_raw = fs::read_to_string(timeline_ledger_path).map_err(|e| e.to_string())?;
    let mut msg_lines = msg_raw.lines();
    let _ = msg_lines.next();
    let mut msg_rows: Vec<MsgRow> = Vec::new();
    for line in msg_lines {
        msg_rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let sync_raw = fs::read_to_string(sync_lattice_path).map_err(|e| e.to_string())?;
    let mut sync_lines = sync_raw.lines();
    let _ = sync_lines.next();
    let mut pairs: Vec<SyncPair> = Vec::new();
    for line in sync_lines {
        pairs.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let mut by_topic: BTreeMap<String, Vec<(u64, i64)>> = BTreeMap::new();
    for p in &pairs {
        by_topic
            .entry(p.topic.clone())
            .or_default()
            .push((p.ref_stamp_ns, p.delta_ns));
    }
    let mut drift_rows = Vec::new();
    for (topic, samples) in by_topic {
        if samples.len() < cfg.drift_min_samples as usize {
            continue;
        }
        let n = samples.len() as f64;
        let sum_x: f64 = samples.iter().map(|(x, _)| *x as f64).sum();
        let sum_y: f64 = samples.iter().map(|(_, y)| *y as f64).sum();
        let x_mean = sum_x / n;
        let y_mean = sum_y / n;
        let mut num = 0.0f64;
        let mut den = 0.0f64;
        for (x, y) in &samples {
            let xd = *x as f64 - x_mean;
            let yd = *y as f64 - y_mean;
            num += xd * yd;
            den += xd * xd;
        }
        let slope = if den.abs() < 1e-9 { 0.0 } else { num / den };
        let intercept = y_mean - slope * x_mean;
        drift_rows.push(DriftRow {
            topic,
            slope: -slope,
            intercept_ns: -intercept,
            sample_count: samples.len() as u32,
        });
    }
    drift_rows.sort_by(|a, b| a.topic.cmp(&b.topic));
    let atlas = SkewAtlas {
        bag_id: meta.bag_id.clone(),
        reference_topic: meta.reference_topic.clone(),
        sync_window_ns: meta.sync_window_ns,
        drop_count: count_drops(&msg_rows),
        sync_pair_count: pairs.len() as u32,
        drift_rows,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&atlas);
    Ok(SkewAtlas {
        audit_digest: digest,
        ..atlas
    })
}

pub fn write_atlas(
    cfg: &Config,
    meta: &ManifestLatch,
    timeline_ledger_path: &str,
    sync_lattice_path: &str,
    output: &Path,
) -> Result<(), String> {
    let atlas = build_atlas(cfg, meta, timeline_ledger_path, sync_lattice_path)?;
    fs::write(output, serde_json::to_string_pretty(&atlas).unwrap()).map_err(|e| e.to_string())
}
