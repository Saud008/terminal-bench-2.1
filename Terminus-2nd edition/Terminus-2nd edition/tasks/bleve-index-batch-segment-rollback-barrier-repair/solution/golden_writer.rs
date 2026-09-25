use crate::errors::BleveError;
use crate::id::allocator::{allocate_doc_ids, commit_doc_ids};
use crate::merge::scheduler::maybe_schedule_merge;
use crate::model::{BatchRecord, BatchSnapshot, SegmentData, SegmentRecord};
use crate::segment::checksum::verify_segment;
use crate::segment::store::{rollback_segment, write_segment};
use crate::state::fs::{ensure_index_dirs, load_root_map, set_open_batch, write_snapshot};
use std::fs;
use std::path::Path;

pub fn ingest_batch(index: &str, batch_path: &Path) -> Result<(), BleveError> {
    let root = ensure_index_dirs(index)?;
    set_open_batch(&root, true)?;

    let lines = fs::read_to_string(batch_path)?
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|line| serde_json::from_str::<BatchRecord>(line))
        .collect::<Result<Vec<_>, _>>()?;

    write_snapshot(&BatchSnapshot {
        index: index.to_string(),
        batch_path: batch_path.display().to_string(),
        record_count: lines.len(),
        status: "open".to_string(),
    })?;

    let map = load_root_map(&root)?;
    let segment_id = map.segments.len() as u64 + 1;
    let doc_ids = allocate_doc_ids(&root, lines.len())?;
    let records = lines
        .into_iter()
        .zip(doc_ids.into_iter())
        .map(|(src, doc_id)| SegmentRecord {
            doc_id,
            id: src.id,
            key: src.key,
            payload: src.payload,
            checksum: src.checksum,
        })
        .collect::<Vec<_>>();

    let segment = SegmentData { segment_id, records };

    if let Err(check_err) = verify_segment(&segment.records) {
        write_snapshot(&BatchSnapshot {
            index: index.to_string(),
            batch_path: batch_path.display().to_string(),
            record_count: segment.records.len(),
            status: "rolled_back".to_string(),
        })?;
        set_open_batch(&root, false)?;
        return Err(BleveError::Message(check_err));
    }

    write_segment(&root, &segment)?;
    commit_doc_ids(&root, segment.records.len())?;
    set_open_batch(&root, false)?;

    maybe_schedule_merge(&root, false, load_root_map(&root)?.segments.len())?;

    write_snapshot(&BatchSnapshot {
        index: index.to_string(),
        batch_path: batch_path.display().to_string(),
        record_count: segment.records.len(),
        status: "committed".to_string(),
    })?;
    Ok(())
}

#[allow(dead_code)]
fn _rollback_written_segment(root: &Path, segment_id: u64) -> Result<(), BleveError> {
    rollback_segment(root, segment_id)
}
