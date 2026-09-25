use std::fs;
use std::path::Path;

use crate::types::{SegmentInput, SegmentRow, StageFile};

pub fn ingest_directory(dir: &str, stage_path: &str) -> Result<(), String> {
    let entries = fs::read_dir(dir).map_err(|e| e.to_string())?;
    let mut names: Vec<String> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .filter(|n| n.ends_with(".json"))
        .collect();
    names.sort();

    let mut segments = Vec::new();
    for (idx, name) in names.iter().enumerate() {
        let path = Path::new(dir).join(name);
        let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let input: SegmentInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        segments.push(SegmentRow {
            segment_id: input.segment_id,
            max_doc: input.max_doc,
            delete_bits: input.delete_bits,
            terms: input.terms,
            source: name.clone(),
            ingest_order: (idx + 1) as u32,
        });
    }

    let prev_seq = crate::staging::load_stage(stage_path)
        .ok()
        .map(|s| s.ingest_seq)
        .unwrap_or(0);
    let stage = StageFile {
        ingest_seq: prev_seq + 1,
        segments,
    };
    crate::staging::save_stage(stage_path, &stage)
}
