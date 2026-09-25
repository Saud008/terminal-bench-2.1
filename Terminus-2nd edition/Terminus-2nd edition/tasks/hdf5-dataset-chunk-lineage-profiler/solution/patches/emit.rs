use crate::hdclp_types::{DatasetLineage, ExportedChunk, LineageReport, StagingSnapshot};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

fn staging_path_for_export(state_dir: &Path) -> PathBuf {
    if let Ok(root) = std::env::var("TB3_STATE_ROOT") {
        PathBuf::from(root).join("staging.json")
    } else {
        state_dir.join("staging.json")
    }
}

pub fn run_export(state_dir: &Path, out_path: &Path) -> Result<(), String> {
    let staging_path = staging_path_for_export(state_dir);
    let raw = fs::read_to_string(&staging_path).map_err(|e| format!("read staging: {e}"))?;
    let snap: StagingSnapshot =
        serde_json::from_str(&raw).map_err(|e| format!("parse staging: {e}"))?;

    let mut datasets: BTreeMap<String, DatasetLineage> = BTreeMap::new();
    for chunk in &snap.chunks {
        let entry = datasets.entry(chunk.dataset_path.clone()).or_insert_with(|| {
            DatasetLineage {
                chunk_count: 0,
                chunks: Vec::new(),
                attribute_lineage: chunk.effective_attrs.clone(),
                coordinate_ok: true,
            }
        });
        entry.chunk_count += 1;
        if !chunk.coord_consistent {
            entry.coordinate_ok = false;
        }
        entry.chunks.push(ExportedChunk {
            chunk_index: chunk.chunk_index,
            origin: chunk.origin.clone(),
            filter_chain_hash: chunk.filter_chain_hash.clone(),
            masked_cells: chunk.masked_cells,
            coord_labels: chunk.coord_labels.clone(),
        });
    }

    for entry in datasets.values_mut() {
        entry.chunks.sort_by_key(|c| c.chunk_index);
    }

    let datasets_body =
        serde_json::to_vec(&datasets).map_err(|e| format!("encode datasets: {e}"))?;
    let export_fingerprint = hex::encode(Sha256::digest(&datasets_body));

    let report = LineageReport {
        version: 1,
        sequence: snap.sequence,
        datasets,
        compression_summary: snap.compression_totals.clone(),
        export_fingerprint,
    };

    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir out: {e}"))?;
    }
    let json = serde_json::to_string(&report).map_err(|e| format!("encode report: {e}"))?;
    fs::write(out_path, format!("{json}
")).map_err(|e| format!("write report: {e}"))?;
    Ok(())
}
