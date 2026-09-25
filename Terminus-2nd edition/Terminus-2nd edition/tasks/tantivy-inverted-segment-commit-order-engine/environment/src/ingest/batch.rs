use crate::segment::{build_postings, default_field_norms, save_segment, Doc, Segment};
use crate::staging::{load_catalog, save_catalog};
use serde::Deserialize;
use std::fs;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Deserialize)]
#[serde(tag = "op", rename_all = "lowercase")]
pub enum BatchOp {
    Add { title: String, body: String },
    Delete { doc_id: u32 },
}

pub fn parse_batch(path: &Path) -> Result<Vec<BatchOp>, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("read batch: {e}"))?;
    let mut ops = Vec::new();
    for (i, line) in raw.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let op: BatchOp =
            serde_json::from_str(line).map_err(|e| format!("line {}: {e}", i + 1))?;
        ops.push(op);
    }
    Ok(ops)
}

pub fn ingest_batch(index: &str, batch_path: &Path) -> Result<String, String> {
    let ops = parse_batch(batch_path)?;
    let mut docs: Vec<Doc> = Vec::new();
    let mut tombstones: Vec<u32> = Vec::new();
    let mut next_id = 0u32;
    for op in ops {
        match op {
            BatchOp::Add { title, body } => {
                docs.push(Doc {
                    doc_id: next_id,
                    title,
                    body,
                });
                next_id += 1;
            }
            BatchOp::Delete { doc_id } => {
                tombstones.push(doc_id);
            }
        }
    }
    tombstones.sort_unstable();
    tombstones.dedup();

    let seg_id = format!(
        "seg-{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| e.to_string())?
            .as_nanos()
    );
    let postings = build_postings(&docs);
    let mut norms = default_field_norms();
    norms.insert("body".to_string(), 3);

    let seg = Segment {
        segment_id: seg_id.clone(),
        docs,
        postings,
        tombstones,
        field_norms: norms,
    };
    save_segment(index, &seg)?;

    let mut cat = load_catalog()?;
    let state = cat.indexes.entry(index.to_string()).or_default();
    state.staging_segment_ids.push(seg_id.clone());
    state.reader_registry.push(seg_id.clone());
    save_catalog(&cat)?;
    Ok(seg_id)
}
