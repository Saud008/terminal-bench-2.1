//! Trace ingest — read head advancement rules in /app/docs/trace-ingest.md.

use crate::model::{IngestManifest, TraceEvent};
use crate::store::LagStore;
use crate::trace_path::resolve_trace_path;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

pub fn ingest_trace(trace_path: &Path, db_path: &Path, manifest_path: &Path) -> Result<IngestManifest, String> {
    let store = LagStore::open(db_path).map_err(|e| e.to_string())?;
    store.set_meta("read_head", 0).map_err(|e| e.to_string())?;
    store.set_meta("gap_events", 0).map_err(|e| e.to_string())?;
    store
        .set_meta("integrity_seed", 0xA5A5A5A5)
        .map_err(|e| e.to_string())?;

    let resolved = resolve_trace_path(trace_path);
    let file = fs::File::open(&resolved).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);
    let mut events_total = 0u64;
    let mut read_head = 0u64;

    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let event: TraceEvent = serde_json::from_str(trimmed).map_err(|e| e.to_string())?;
        events_total += 1;

        match event {
            TraceEvent::LateFrame { frame_seq } => {
                if frame_seq < read_head {
                    // rejected — do not move read_head
                } else {
                    read_head = frame_seq + 1;
                }
            }
            TraceEvent::SnapshotDelta {
                snapshot_seq,
                base_seq,
                state_xor,
            } => {
                store
                    .insert_snapshot_delta(snapshot_seq, base_seq, state_xor)
                    .map_err(|e| e.to_string())?;
                if snapshot_seq >= read_head {
                    read_head = snapshot_seq + 1;
                }
            }
            TraceEvent::SnapshotGap { .. } => {
                store.bump_gap_events().map_err(|e| e.to_string())?;
            }
            _ => {}
        }
    }

    store.set_meta("read_head", read_head).map_err(|e| e.to_string())?;

    let manifest = IngestManifest {
        trace_path: resolved.display().to_string(),
        events_total,
        read_head,
    };

    let parent = manifest_path.parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    fs::write(
        manifest_path,
        serde_json::to_string_pretty(&manifest).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    Ok(manifest)
}
