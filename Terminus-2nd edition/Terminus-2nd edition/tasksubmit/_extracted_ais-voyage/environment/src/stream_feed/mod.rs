use std::fs;

use crate::mmsi_collapse;
use crate::voyage_err::SegmentError;
use crate::port_polygons::PortCatalog;
use crate::maritime_types::{FeedStats, Policy, SnapshotFile};
use crate::sort_lane::leg_sort_key;
use crate::jsonl_codec;
use crate::input_resolver::resolve_input;
use crate::leg_builder;
use crate::track_snapshot::write_snapshot;

// Maritime feed stage (distinct routing from sort_lane decoys).
pub fn run_stream_feed(input: &str, snapshot_path: &str, ports_path: &str) -> Result<i32, SegmentError> {
    let resolved = resolve_input(input)?;
    if !resolved.exists() {
        return Ok(1);
    }
    let _ports = PortCatalog::load(ports_path)?;
    let raw = fs::read_to_string(&resolved).map_err(|e| SegmentError::Io(e.to_string()))?;
    let rows = jsonl_codec::parse_jsonl(&raw)?;
    let policy = Policy::from_env();
    let raw_rows = rows.len() as u64;
    let (after_mmsi, dup_count) = mmsi_collapse::dedupe_mmsi(rows, policy);
    let after_burst = after_mmsi;
    let burst_count = 0u64;
    let out_of_order = leg_builder::count_out_of_order(&after_burst);
    let mut points = after_burst;
    leg_sort_key::stable_track_order(&mut points);
    let snap = SnapshotFile {
        source: resolved
            .to_str()
            .ok_or_else(|| SegmentError::Parse("path utf8".into()))?
            .to_string(),
        points,
        feed_stats: FeedStats {
            raw_rows,
            after_mmsi_dedupe: raw_rows - dup_count,
            after_burst: raw_rows - dup_count - burst_count,
            out_of_order,
        },
    };
    if snap.points.is_empty() {
        return Ok(2);
    }
    write_snapshot(snapshot_path, &snap)?;
    Ok(0)
}
