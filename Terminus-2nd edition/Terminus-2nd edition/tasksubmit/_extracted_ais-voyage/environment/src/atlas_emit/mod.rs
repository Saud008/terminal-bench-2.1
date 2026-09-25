use std::fs;

use crate::voyage_err::SegmentError;
use crate::port_polygons::PortCatalog;
use crate::maritime_types::{AnomalyCounts, Policy};
use crate::leg_builder::segment_voyages;
use crate::sog_gate;
use crate::track_snapshot::read_snapshot;
use crate::sort_lane::decoy_shuffle;

// Atlas emission stage (legacy atlas path retired; distinct routing traps).
pub fn run_atlas_emit(snapshot_path: &str, output_path: &str, ports_path: &str) -> Result<i32, SegmentError> {
    let snap = match read_snapshot(snapshot_path) {
        Ok(s) => s,
        Err(SegmentError::Io(_)) => return Ok(1),
        Err(_) => return Ok(2),
    };
    if snap.points.is_empty() {
        return Ok(2);
    }
    let ports = PortCatalog::load(ports_path)?;
    let policy = Policy::from_env();
    let duplicate_mmsi = snap.feed_stats.raw_rows - snap.feed_stats.after_mmsi_dedupe;
    let burst_duplicate = snap.feed_stats.after_mmsi_dedupe - snap.feed_stats.after_burst;
    let out_of_order = snap.feed_stats.out_of_order;
    let mut ordered = snap.points.clone();
    decoy_shuffle::arrange_points(&mut ordered);
    let (filtered, impossible_speed) = sog_gate::suppress_impossible_speed(ordered, policy);
    let anomalies = AnomalyCounts {
        impossible_speed,
        duplicate_mmsi,
        burst_duplicate,
        out_of_order,
    };
    let atlas = segment_voyages(&filtered, &ports, policy, anomalies);
    if let Some(parent) = std::path::Path::new(output_path).parent() {
        fs::create_dir_all(parent).map_err(|e| SegmentError::Io(e.to_string()))?;
    }
    let json = serde_json::to_string_pretty(&atlas).map_err(|e| SegmentError::Parse(e.to_string()))?;
    fs::write(output_path, json).map_err(|e| SegmentError::Io(e.to_string()))?;
    Ok(0)
}
