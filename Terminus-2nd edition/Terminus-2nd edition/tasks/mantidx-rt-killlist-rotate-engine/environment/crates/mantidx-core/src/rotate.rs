use crate::binlog::checkpoint_after_rotate;
use crate::killlist::apply_killlist_for_rotate;
use crate::model::RotateAudit;
use crate::segment::{
    current_ram_segment, load_rotate_meta, next_disk_chunk_id, next_ram_segment_id, save_rotate_meta,
};
use crate::store::{open_db, reassign_segment};
use std::fs;
use std::path::Path;

fn rotate_audit_path(state: &Path) -> std::path::PathBuf {
    state.join("rotate-audit.json")
}

pub fn save_rotate_audit(state: &Path, audit: &RotateAudit) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(audit).map_err(|e| e.to_string())?;
    fs::write(rotate_audit_path(state), raw).map_err(|e| e.to_string())
}

pub fn run_rotate(state: &Path, db: &Path) -> Result<RotateAudit, String> {
    let mut meta = load_rotate_meta(state)?;
    let ram = current_ram_segment(state)?;
    let disk_id = next_disk_chunk_id(state)?;

    let conn = open_db(db).map_err(|e| e.to_string())?;
    reassign_segment(&conn, &ram, &disk_id, "disk").map_err(|e| e.to_string())?;

    meta.disk_chunks.push(disk_id.clone());
    meta.rotate_seq += 1;
    let rotate_seq = meta.rotate_seq;

    save_rotate_meta(state, &meta)?;
    let disk_published_before_killlist = true;

    let (_applied, killlist_applied_on_ram_tier) = apply_killlist_for_rotate(state, db, &ram)?;

    let checkpoint_seq = checkpoint_after_rotate(state, db, rotate_seq)?;

    let new_ram = next_ram_segment_id(state)?;
    meta.active_ram.push(new_ram);
    save_rotate_meta(state, &meta)?;

    let audit = RotateAudit {
        disk_published_before_killlist,
        killlist_applied: true,
        killlist_applied_on_ram_tier,
        disk_chunk_id: disk_id,
        checkpoint_seq,
    };
    save_rotate_audit(state, &audit)?;
    Ok(audit)
}
