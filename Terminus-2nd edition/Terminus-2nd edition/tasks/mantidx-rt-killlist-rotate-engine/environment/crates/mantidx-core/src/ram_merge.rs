use crate::model::MergeRamAudit;
use crate::segment::{load_ram_segments, save_ram_segments};
use crate::store::{docs_for_segment, open_db, reassign_segment};
use std::fs;
use std::path::Path;

fn merge_audit_path(state: &Path) -> std::path::PathBuf {
    state.join("merge-ram-audit.json")
}

pub fn save_merge_audit(state: &Path, audit: &MergeRamAudit) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(audit).map_err(|e| e.to_string())?;
    fs::write(merge_audit_path(state), raw).map_err(|e| e.to_string())
}

pub fn run_merge_ram(state: &Path, db: &Path, left: &str, right: &str) -> Result<MergeRamAudit, String> {
    let file = load_ram_segments(state)?;
    if !file.segments.iter().any(|s| s.segment_id == left)
        || !file.segments.iter().any(|s| s.segment_id == right)
    {
        return Err("unknown ram segment".into());
    }

    let merged_into = if left < right {
        left.to_string()
    } else {
        right.to_string()
    };
    let other = if merged_into == left {
        right.to_string()
    } else {
        left.to_string()
    };

    let conn = open_db(db).map_err(|e| e.to_string())?;
    let _left_docs = docs_for_segment(&conn, left).map_err(|e| e.to_string())?;
    let _right_docs = docs_for_segment(&conn, right).map_err(|e| e.to_string())?;

    reassign_segment(&conn, &other, &merged_into, "ram").map_err(|e| e.to_string())?;

    let mut new_file = file.clone();
    new_file.segments.retain(|s| s.segment_id != left && s.segment_id != right);
    let left_meta = file.segments.iter().find(|s| s.segment_id == left).cloned();
    let right_meta = file.segments.iter().find(|s| s.segment_id == right).cloned();
    let mut bitmap = Vec::new();
    if let Some(m) = left_meta {
        bitmap.extend(m.deleted_bitmap);
    }
    if let Some(m) = right_meta {
        bitmap.extend(m.deleted_bitmap);
    }
    let deleted_respected = bitmap.iter().all(|doc_id| {
        conn.query_row(
            "SELECT killed FROM docs WHERE doc_id = ?1",
            rusqlite::params![doc_id],
            |row| row.get::<_, i64>(0),
        )
        .map(|k| k == 1)
        .unwrap_or(false)
    });
    new_file.segments.push(crate::model::RamSegmentMeta {
        segment_id: merged_into.clone(),
        deleted_bitmap: bitmap,
        segment_order: file.segments.len() as i64,
    });
    save_ram_segments(state, &new_file)?;

    let audit = MergeRamAudit {
        left: left.to_string(),
        right: right.to_string(),
        merged_into: merged_into.clone(),
        deleted_respected,
    };
    save_merge_audit(state, &audit)?;
    Ok(audit)
}
