use crate::commit::wal::load_wal_record;
use crate::segment::{load_segment, live_doc_count, posting_checksum};
use crate::staging::{dangling_readers, load_catalog, IndexSnapshot};
use serde::Serialize;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct StatsReport {
    pub index: String,
    pub live_doc_count: u32,
    pub staging_segments: u32,
    pub committed_segments: u32,
    pub posting_checksum: u64,
    pub dangling_reader_count: u32,
    pub wal_fsynced: bool,
    pub commit_lock_released_before_wal: bool,
    pub field_norm_title: u32,
    pub field_norm_body: u32,
}

pub fn stats_for_index(index: &str) -> Result<StatsReport, String> {
    let cat = load_catalog()?;
    let state = cat
        .indexes
        .get(index)
        .ok_or_else(|| format!("index {index} missing"))?;

    let mut live = state.committed_live_docs;
    if live == 0 {
        for id in &state.committed_segment_ids {
            let seg = load_segment(index, id)?;
            live += live_doc_count(&seg);
        }
    }

    let mut checksum = 0u64;
    for id in &state.committed_segment_ids {
        let seg = load_segment(index, id)?;
        checksum ^= posting_checksum(&seg);
    }

    let norms_title;
    let norms_body;
    if let Some(last) = state.committed_segment_ids.last() {
        let seg = load_segment(index, last)?;
        norms_title = *seg.field_norms.get("title").unwrap_or(&0);
        norms_body = *seg.field_norms.get("body").unwrap_or(&0);
    } else {
        norms_title = 0;
        norms_body = 0;
    }

    let wal = load_wal_record();
    let wal_rec = wal.unwrap_or_default();

    Ok(StatsReport {
        index: index.to_string(),
        live_doc_count: live,
        staging_segments: state.staging_segment_ids.len() as u32,
        committed_segments: state.committed_segment_ids.len() as u32,
        posting_checksum: checksum,
        dangling_reader_count: dangling_readers(state),
        wal_fsynced: wal_rec.wal_fsynced,
        commit_lock_released_before_wal: wal_rec.lock_released_before_fsync,
        field_norm_title: norms_title,
        field_norm_body: norms_body,
    })
}

pub fn load_snapshot() -> Result<IndexSnapshot, String> {
    let raw = std::fs::read_to_string("/app/state/index-snapshot.json")
        .map_err(|e| format!("read snapshot: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse snapshot: {e}"))
}

pub fn snapshot_path() -> &'static Path {
    Path::new("/app/state/index-snapshot.json")
}
