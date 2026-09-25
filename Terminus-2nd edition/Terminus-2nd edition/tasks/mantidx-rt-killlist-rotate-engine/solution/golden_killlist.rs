use crate::model::{KillEntry, KilllistState};
use crate::segment::load_ram_segments;
use crate::store::{docs_matching, doc_tier, mark_killed, open_db};
use std::fs;
use std::path::{Path, PathBuf};

pub fn killlist_path(state: &Path) -> PathBuf {
    state.join("killlist.json")
}

pub fn load_killlist(state: &Path) -> Result<KilllistState, String> {
    let path = killlist_path(state);
    if !path.exists() {
        return Ok(KilllistState {
            pending: Vec::new(),
            applied: false,
        });
    }
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn save_killlist(state: &Path, kl: &KilllistState) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(kl).map_err(|e| e.to_string())?;
    fs::write(killlist_path(state), raw).map_err(|e| e.to_string())
}

pub fn queue_delete(state: &Path, db: &Path, token: &str) -> Result<usize, String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let hits = docs_matching(&conn, token).map_err(|e| e.to_string())?;
    let ram = load_ram_segments(state)?;
    let mut kl = load_killlist(state)?;
    let mut count = 0usize;
    for (doc_id, _body, segment_id, _killed) in hits {
        let order = ram
            .segments
            .iter()
            .find(|s| s.segment_id == segment_id)
            .map(|s| s.segment_order)
            .unwrap_or(0);
        kl.pending.push(KillEntry {
            doc_id,
            segment_id: segment_id.clone(),
            segment_order: order,
        });
        mark_deleted_in_bitmap(state, doc_id, &segment_id)?;
        count += 1;
    }
    kl.applied = false;
    save_killlist(state, &kl)?;
    Ok(count)
}

pub fn merge_pending_killlist(entries: &mut [KillEntry]) -> Vec<KillEntry> {
    entries.sort_by_key(|e| (e.segment_order, e.doc_id));
    entries.to_vec()
}

fn killlist_merge_audit_path(state: &Path) -> PathBuf {
    state.join("killlist-merge-audit.json")
}

pub fn save_killlist_merge_audit(state: &Path, merged: &[KillEntry]) -> Result<(), String> {
    let merged_order: Vec<_> = merged
        .iter()
        .map(|e| {
            serde_json::json!({
                "doc_id": e.doc_id,
                "segment_id": e.segment_id,
                "segment_order": e.segment_order,
            })
        })
        .collect();
    let raw = serde_json::to_string(&serde_json::json!({"merged_order": merged_order}))
        .map_err(|e| e.to_string())?;
    fs::write(killlist_merge_audit_path(state), raw).map_err(|e| e.to_string())
}

pub fn apply_killlist_for_rotate(
    state: &Path,
    db: &Path,
    rotating_segment: &str,
) -> Result<(usize, bool), String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let mut kl = load_killlist(state)?;
    let mut scoped: Vec<KillEntry> = kl
        .pending
        .iter()
        .filter(|e| e.segment_id == rotating_segment)
        .cloned()
        .collect();
    let merged = merge_pending_killlist(&mut scoped);
    save_killlist_merge_audit(state, &merged)?;
    let mut applied_on_ram = true;
    let mut applied = 0usize;
    for entry in &merged {
        let tier = doc_tier(&conn, entry.doc_id).map_err(|e| e.to_string())?;
        if tier != "ram" {
            applied_on_ram = false;
        }
        mark_killed(&conn, entry.doc_id).map_err(|e| e.to_string())?;
        applied += 1;
    }
    kl.pending.retain(|e| e.segment_id != rotating_segment);
    kl.applied = kl.pending.is_empty();
    save_killlist(state, &kl)?;
    Ok((applied, applied_on_ram))
}

pub fn mark_deleted_in_bitmap(state: &Path, doc_id: i64, segment_id: &str) -> Result<(), String> {
    let mut file = load_ram_segments(state)?;
    if let Some(seg) = file.segments.iter_mut().find(|s| s.segment_id == segment_id) {
        if !seg.deleted_bitmap.contains(&doc_id) {
            seg.deleted_bitmap.push(doc_id);
        }
    }
    crate::segment::save_ram_segments(state, &file)
}
