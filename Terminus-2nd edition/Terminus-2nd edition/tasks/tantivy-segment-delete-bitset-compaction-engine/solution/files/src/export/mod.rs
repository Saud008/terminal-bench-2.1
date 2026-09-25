use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};

use crate::merge;
use crate::merge::postings;
use crate::staging;
use crate::stats;
use crate::types::{MergeState, SegmentStats};

pub fn merge_export(stage_path: &str, stats_path: &str, checksum_path: &str, state_path: &str, pass: u32) -> Result<(), String> {
    let stage = staging::load_stage(stage_path)?;
    if stage.segments.is_empty() {
        return Err("no segments in staging".into());
    }

    let seed = std::env::var("TB3_SEGMENT_SEED")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);

    let merged = merge::merge_segments(&stage.segments, pass, seed);
    let stats_doc = stats::rollup::attach_merge_pass(merged, pass);

    let _term_total = stats::rollup::term_count(&stats_doc);
    write_stats_with_norm_width(&stats_doc, stats_path)?;
    let digest = checksum_from_stats(&stats_doc)?;
    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    fs::write(checksum_path, format!("{digest}\n")).map_err(|e| e.to_string())?;

    save_merge_state(
        state_path,
        &MergeState {
            delete_bits: stats_doc.delete_bits.clone(),
            merge_pass: pass,
        },
    )
}

fn write_stats_with_norm_width(stats: &SegmentStats, path: &str) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;

    let mut doc = serde_json::to_value(stats).map_err(|e| e.to_string())?;
    if let Some(terms) = doc.get_mut("terms").and_then(|t| t.as_array_mut()) {
        for term in terms {
            if let Some(norm) = term.get("norm").and_then(|n| n.as_u64()) {
                term["norm"] = postings::norm_json_value(norm as u8);
            }
        }
    }
    let pretty = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    fs::write(path, format!("{pretty}\n")).map_err(|e| e.to_string())
}

pub fn checksum_from_stats(stats: &SegmentStats) -> Result<String, String> {
    let mut canonical = stats.clone();
    canonical.merge_pass = 0;
    for term in &mut canonical.terms {
        term.norm = postings::export_norm(term.norm);
    }
    let bytes = serde_json::to_vec(&canonical).map_err(|e| e.to_string())?;
    let hash = Sha256::digest(bytes);
    Ok(hex::encode(hash))
}

fn save_merge_state(path: &str, state: &MergeState) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(state).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
