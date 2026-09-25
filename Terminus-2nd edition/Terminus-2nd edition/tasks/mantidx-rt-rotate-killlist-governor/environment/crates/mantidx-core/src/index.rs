use crate::segment::{
    current_ram_segment, load_ram_segments, load_rotate_meta, next_ram_segment_id, save_ram_segments,
    save_rotate_meta,
};
use crate::store::{docs_for_segment, enqueue_binlog, insert_doc, open_db};
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};

fn resolve_batch(batch: &Path) -> PathBuf {
    if batch.is_relative() {
        if let Ok(tb3) = std::env::var("TB3_DOCS_DIR") {
            let root = PathBuf::from(tb3);
            if root.is_absolute() {
                return root.join(batch);
            }
        }
    }
    batch.to_path_buf()
}

pub fn index_batch(db: &Path, batch: &Path, state: &Path) -> Result<usize, String> {
    let batch = resolve_batch(batch);
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let mut segment = current_ram_segment(state)?;
    let existing = docs_for_segment(&conn, &segment).map_err(|e| e.to_string())?;
    if !existing.is_empty() {
        segment = next_ram_segment_id(state)?;
        let mut meta = load_rotate_meta(state).map_err(|e| e.to_string())?;
        meta.active_ram.push(segment.clone());
        save_rotate_meta(state, &meta).map_err(|e| e.to_string())?;
    }
    let raw = fs::read_to_string(batch).map_err(|e| e.to_string())?;
    let mut count = 0usize;
    for line in raw.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let v: Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
        let doc_id = v
            .get("doc_id")
            .and_then(|x| x.as_i64())
            .ok_or("missing doc_id")?;
        let body = v
            .get("body")
            .and_then(|x| x.as_str())
            .ok_or("missing body")?
            .to_string();
        insert_doc(&conn, doc_id, &body, &segment, "ram").map_err(|e| e.to_string())?;
        enqueue_binlog(&conn, doc_id, &body).map_err(|e| e.to_string())?;
        count += 1;
    }
    let mut file = load_ram_segments(state)?;
    if !file.segments.iter().any(|s| s.segment_id == segment) {
        let order = file.segments.len() as i64 + 1;
        file.segments.push(crate::model::RamSegmentMeta {
            segment_id: segment.clone(),
            deleted_bitmap: Vec::new(),
            segment_order: order,
        });
        save_ram_segments(state, &file)?;
    }
    Ok(count)
}
