use crate::types::{BlockAnomaly, ConsistencyReport, PhasedBlock, SamplePhaseMatrix};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn audit_digest(report: &ConsistencyReport) -> String {
    let mut block_ids: Vec<String> = report.blocks.iter().map(|b| b.block_id.clone()).collect();
    block_ids.sort();
    let body = serde_json::json!({
        "anomaly_count": report.anomaly_count,
        "block_count": report.block_count,
        "block_ids": block_ids,
        "run_id": report.run_id,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

fn load_edge_list(path: &Path) -> Result<(Vec<PhasedBlock>, Vec<BlockAnomaly>), String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut block_map: BTreeMap<String, PhasedBlock> = BTreeMap::new();
    let mut anomalies = Vec::new();
    for line in raw.lines().skip(1) {
        let rec: serde_json::Value =
            serde_json::from_str(line).map_err(|e| format!("edge parse: {e}"))?;
        match rec.get("record_type").and_then(|v| v.as_str()) {
            Some("edge") => {
                let block_id = rec["block_id"].as_str().unwrap_or("").to_string();
                let entry = block_map.entry(block_id.clone()).or_insert_with(|| PhasedBlock {
                    block_id: block_id.clone(),
                    chrom: rec["chrom"].as_str().unwrap_or("").to_string(),
                    ps_tag: rec["ps_tag"].as_str().unwrap_or("").to_string(),
                    variant_count: rec["variant_count"].as_u64().unwrap_or(0) as u32,
                    sample_ids: Vec::new(),
                });
                let sid = rec["sample_id"].as_str().unwrap_or("").to_string();
                if !sid.is_empty() && !entry.sample_ids.contains(&sid) {
                    entry.sample_ids.push(sid);
                }
            }
            Some("anomaly") => {
                anomalies.push(BlockAnomaly {
                    anomaly_id: rec["anomaly_id"].as_str().unwrap_or("").to_string(),
                    chrom: rec["chrom"].as_str().unwrap_or("").to_string(),
                    ps_tag: rec["ps_tag"].as_str().unwrap_or("").to_string(),
                    anomaly_type: rec["anomaly_type"].as_str().unwrap_or("").to_string(),
                    sample_ids: rec["sample_ids"]
                        .as_array()
                        .map(|a| {
                            a.iter()
                                .filter_map(|v| v.as_str().map(str::to_string))
                                .collect()
                        })
                        .unwrap_or_default(),
                    variant_positions: rec["variant_positions"]
                        .as_array()
                        .map(|a| {
                            a.iter()
                                .filter_map(|v| v.as_u64().map(|n| n as u32))
                                .collect()
                        })
                        .unwrap_or_default(),
                });
            }
            _ => {}
        }
    }
    let mut blocks: Vec<PhasedBlock> = block_map.into_values().collect();
    blocks.sort_by(|a, b| a.block_id.cmp(&b.block_id));
    for block in &mut blocks {
        block.sample_ids.sort();
    }
    anomalies.sort_by(|a, b| a.anomaly_id.cmp(&b.anomaly_id));
    Ok((blocks, anomalies))
}

pub fn build_report(cfg: &crate::types::Config, run_id: &str) -> Result<ConsistencyReport, String> {
    let _staging: SamplePhaseMatrix = serde_json::from_str(
        &fs::read_to_string(format!("{}/{}.json", cfg.sample_matrix_dir, run_id))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let edge_path = format!("{}/{}.jsonl", cfg.block_edge_list_dir, run_id);
    let (mut blocks, mut anomalies) = load_edge_list(Path::new(&edge_path))?;
    blocks.sort_by(|a, b| a.block_id.cmp(&b.block_id));
    anomalies.sort_by(|a, b| a.anomaly_id.cmp(&b.anomaly_id));
    let report = ConsistencyReport {
        run_id: run_id.to_string(),
        block_count: blocks.len() as u32,
        anomaly_count: anomalies.len() as u32,
        blocks,
        anomalies,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&report);
    Ok(ConsistencyReport {
        audit_digest: digest,
        ..report
    })
}

pub fn write_report(cfg: &crate::types::Config, run_id: &str, output: &Path) -> Result<(), String> {
    let report = build_report(cfg, run_id)?;
    fs::write(
        output,
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
