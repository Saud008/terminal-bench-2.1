use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::io::fastq::{parse_fastq_record, FastqRecord};
use crate::staging;
use crate::types::{LaneConfig, LanesFile, ManifestFile, StagedPair, StagingFile};

pub fn ingest_reads(
    reads_dir: &str,
    manifest_path: &str,
    lanes_path: &str,
    staging_path: &str,
) -> Result<(), String> {
    let manifest_raw = fs::read_to_string(manifest_path).map_err(|e| e.to_string())?;
    let manifest: ManifestFile = serde_json::from_str(&manifest_raw).map_err(|e| e.to_string())?;
    let lanes_raw = fs::read_to_string(lanes_path).map_err(|e| e.to_string())?;
    let lanes: LanesFile = serde_json::from_str(&lanes_raw).map_err(|e| e.to_string())?;

    let precedence_order = if lanes.precedence_order == "lane_first" {
        "lane_first".to_string()
    } else {
        manifest.precedence_order.clone()
    };

    let mut pairs = Vec::new();
    for lane in &lanes.lanes {
        let lane_dir = Path::new(reads_dir).join(&lane.lane_id);
        if !lane_dir.is_dir() {
            continue;
        }
        collect_lane_pairs(&lane_dir, lane, manifest.barcode_length, manifest.umi_length, &mut pairs)?;
    }

    let prev_seq = staging::load_staging(staging_path)
        .ok()
        .map(|s| s.ingest_seq)
        .unwrap_or(0);

    let staging = StagingFile {
        ingest_seq: prev_seq + 1,
        precedence_order,
        mismatch_budget: manifest.mismatch_budget,
        umi_length: manifest.umi_length,
        barcode_length: manifest.barcode_length,
        samples_global: manifest.samples.clone(),
        lanes: lanes.lanes.clone(),
        pairs,
    };

    staging::save_staging(staging_path, &staging)
}

fn collect_lane_pairs(
    lane_dir: &Path,
    lane: &LaneConfig,
    barcode_len: usize,
    umi_len: usize,
    out: &mut Vec<StagedPair>,
) -> Result<(), String> {
    let mut r1_map: HashMap<String, FastqRecord> = HashMap::new();
    let mut r2_map: HashMap<String, FastqRecord> = HashMap::new();

    for entry in fs::read_dir(lane_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let name = entry.file_name().to_string_lossy().into_owned();
        if name.ends_with("_R1.fastq") {
            let pair_id = name.trim_end_matches("_R1.fastq").to_string();
            let rec = parse_fastq_record(&entry.path(), barcode_len, umi_len)?;
            r1_map.insert(pair_id, rec);
        } else if name.ends_with("_R2.fastq") {
            let pair_id = name.trim_end_matches("_R2.fastq").to_string();
            let rec = parse_fastq_record(&entry.path(), barcode_len, umi_len)?;
            r2_map.insert(pair_id, rec);
        }
    }

    for (pair_id, r1) in &r1_map {
        if let Some(r2) = r2_map.get(pair_id) {
            out.push(StagedPair {
                pair_id: pair_id.clone(),
                lane_id: lane.lane_id.clone(),
                r1_barcode: r1.barcode.clone(),
                r1_umi: r1.umi.clone(),
                r2_umi: r2.umi.clone(),
            });
        }
    }

    Ok(())
}
