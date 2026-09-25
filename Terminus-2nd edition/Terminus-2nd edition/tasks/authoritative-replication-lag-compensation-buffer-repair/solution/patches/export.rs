//! Snapshot export and integrity chain — /app/docs/snapshot-export.md.

use crate::model::{ExportAudit, SnapshotBundle};
use crate::snapshot::SnapshotMerger;
use crate::store::LagStore;
use std::fs;
use std::path::Path;

pub fn export_snapshot_bundle(
    db_path: &Path,
    bundle_path: &Path,
    audit_path: &Path,
) -> Result<ExportAudit, String> {
    let store = LagStore::open(db_path).map_err(|e| e.to_string())?;
    let deltas = store.load_snapshot_deltas().map_err(|e| e.to_string())?;
    if deltas.is_empty() {
        return Err("no snapshot deltas ingested".into());
    }
    let gap_events = store.gap_event_count().map_err(|e| e.to_string())?;

    let mut merger = SnapshotMerger::new();
    for (seq, base, xor) in deltas {
        merger.push_delta(seq, base, xor);
    }
    merger.set_gap_fills(gap_events);

    let snapshots = merger.merge_rows();
    let merged_state_hash = merger.merged_state_hash();
    let integrity_chain = store
        .integrity_seed()
        .map_err(|e| e.to_string())?
        ^ merged_state_hash;

    let bundle = SnapshotBundle {
        snapshots,
        merged_state_hash,
        gap_fills: merger.gap_fills(),
        integrity_chain,
    };

    let parent = bundle_path.parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    fs::write(
        bundle_path,
        serde_json::to_string_pretty(&bundle).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    let export_seq = store
        .record_export(merged_state_hash, integrity_chain)
        .map_err(|e| e.to_string())?;

    let audit = ExportAudit {
        snapshot_count: bundle.snapshots.len() as u64,
        merged_state_hash,
        integrity_chain,
        export_seq,
    };

    let audit_parent = audit_path.parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(audit_parent).map_err(|e| e.to_string())?;
    fs::write(
        audit_path,
        serde_json::to_string_pretty(&audit).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    Ok(audit)
}
