use crate::error::Result;
use crate::model::ExportDoc;
use crate::route::build_export;
use crate::snapshot::read_decode_snapshot;

pub fn publish_from_snapshot() -> Result<ExportDoc> {
    let snap = read_decode_snapshot()?;
    build_export(
        snap.frames,
        &snap.seed,
        snap.checkpoint_frame_count,
        snap.deduped_count,
        snap.stale_seq_dropped,
        &snap.diff_rows,
    )
}
