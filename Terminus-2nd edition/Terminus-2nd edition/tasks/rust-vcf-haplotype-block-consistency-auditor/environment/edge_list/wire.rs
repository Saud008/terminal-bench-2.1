use crate::block_consistency;
use crate::ps_group;
use crate::types::{BlockAnomaly, PhasedBlock, SamplePhaseMatrix};
use std::collections::BTreeSet;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

pub fn wire_blocks(cfg: &crate::types::Config, run_id: &str) -> Result<PathBuf, String> {
    let matrix_path = PathBuf::from(&cfg.sample_matrix_dir).join(format!("{run_id}.json"));
    let matrix: SamplePhaseMatrix =
        serde_json::from_str(&fs::read_to_string(&matrix_path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let groups = ps_group::group_variants(&matrix.variant_catalog);
    let mut blocks = Vec::new();
    for (idx, (key, vars)) in groups.iter().enumerate() {
        let chrom = vars.first().map(|v| v.chrom.clone()).unwrap_or_default();
        let ps_tag = key
            .split_once(':')
            .map(|(_, ps)| ps.to_string())
            .unwrap_or_else(|| key.clone());
        let mut sample_ids: BTreeSet<String> = BTreeSet::new();
        for v in vars {
            for gt in &v.genotypes {
                sample_ids.insert(gt.sample_id.clone());
            }
        }
        blocks.push(PhasedBlock {
            block_id: format!("blk{:03}", idx + 1),
            chrom,
            ps_tag,
            variant_count: vars.len() as u32,
            sample_ids: sample_ids.into_iter().collect(),
        });
    }
    let anomalies = block_consistency::detect_anomalies(&matrix.variant_catalog);
    let edge_path = PathBuf::from(&cfg.block_edge_list_dir).join(format!("{run_id}.jsonl"));
    let prev_gen = if edge_path.exists() {
        let raw = fs::read_to_string(&edge_path).map_err(|e| e.to_string())?;
        raw.lines()
            .next()
            .and_then(|line| serde_json::from_str::<serde_json::Value>(line).ok())
            .and_then(|v| v.get("merge_generation").and_then(|g| g.as_u64()))
            .unwrap_or(0) as u32
    } else {
        0
    };
    fs::create_dir_all(&cfg.block_edge_list_dir).map_err(|e| e.to_string())?;
    let mut out = fs::File::create(&edge_path).map_err(|e| e.to_string())?;
    let header = serde_json::json!({
        "record_type": "meta",
        "run_id": run_id,
        "merge_generation": prev_gen + 1,
    });
    writeln!(out, "{}", header.to_string()).map_err(|e| e.to_string())?;
    for block in &blocks {
        for sample_id in &block.sample_ids {
            let edge = serde_json::json!({
                "record_type": "edge",
                "block_id": block.block_id,
                "chrom": block.chrom,
                "ps_tag": block.ps_tag,
                "sample_id": sample_id,
                "variant_count": block.variant_count,
            });
            writeln!(out, "{}", edge.to_string()).map_err(|e| e.to_string())?;
        }
    }
    for anomaly in &anomalies {
        write_anomaly_line(&mut out, anomaly)?;
    }
    Ok(edge_path)
}

fn write_anomaly_line(out: &mut fs::File, anomaly: &BlockAnomaly) -> Result<(), String> {
    let line = serde_json::json!({
        "record_type": "anomaly",
        "anomaly_id": anomaly.anomaly_id,
        "chrom": anomaly.chrom,
        "ps_tag": anomaly.ps_tag,
        "anomaly_type": anomaly.anomaly_type,
        "sample_ids": anomaly.sample_ids,
        "variant_positions": anomaly.variant_positions,
    });
    writeln!(out, "{}", line.to_string()).map_err(|e| e.to_string())
}
