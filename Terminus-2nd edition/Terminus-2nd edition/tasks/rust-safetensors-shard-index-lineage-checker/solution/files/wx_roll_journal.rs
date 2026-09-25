use crate::wx_bundle_read::read_manifest_dir;
use crate::wx_width_table::wx_payload_units;
use crate::wx_parent_bind::wx_anchor_fold;
use crate::wx_digest_seal::wx_seal_slice;
use crate::wx_span_gate::wx_guard_window;
use crate::wx_frame_parse::parse_shard_file;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedRow {
    pub manifest_id: String,
    pub tensor: String,
    pub shard_file: String,
    pub dtype: String,
    pub shape: Vec<u64>,
    pub offset_start: u64,
    pub offset_end: u64,
    pub payload_fingerprint: String,
    pub base_model_hash: String,
    pub lineage_ok: bool,
    pub run_seq: u32,
}

pub fn wx_roll_journal(
    manifest_dir: &Path,
    shard_root: &Path,
    journal_path: &Path,
) -> Result<(), String> {
    let docs = read_manifest_dir(manifest_dir)?;
    let mut lines = Vec::new();
    let mut run_seq = 0u32;
    for doc in docs {
        for shard in &doc.shards {
            let shard_path = shard_root.join(&shard.shard_file);
            let parsed = parse_shard_file(&shard_path)?;
            for spec in &shard.tensors {
                let header = parsed
                    .tensors
                    .get(&spec.name)
                    .ok_or_else(|| format!("missing tensor {}", spec.name))?;
                wx_guard_window(&shard_path, header, &parsed)?;
                let expected = wx_payload_units(&spec.dtype, &spec.shape)
                    .ok_or_else(|| format!("unknown dtype {}", spec.dtype))?;
                let span = header.data_offsets[1] - header.data_offsets[0];
                if span != expected {
                    return Err(format!("span mismatch for {}", spec.name));
                }
                let cs = wx_seal_slice(
                    &shard_path,
                    header.data_offsets[0],
                    header.data_offsets[1],
                )?;
                let row = StagedRow {
                    manifest_id: doc.manifest_id.clone(),
                    tensor: spec.name.clone(),
                    shard_file: shard.shard_file.clone(),
                    dtype: spec.dtype.clone(),
                    shape: spec.shape.clone(),
                    offset_start: header.data_offsets[0],
                    offset_end: header.data_offsets[1],
                    payload_fingerprint: cs,
                    base_model_hash: doc.base_model_hash.clone(),
                    lineage_ok: wx_anchor_fold(&doc),
                    run_seq,
                };
                run_seq += 1;
                lines.push(serde_json::to_string(&row).map_err(|e| e.to_string())?);
            }
        }
    }
    fs::write(journal_path, format!("{}
", lines.join("
"))).map_err(|e| e.to_string())
}

pub fn wx_read_journal(path: &Path) -> Result<Vec<StagedRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}
