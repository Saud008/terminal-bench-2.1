use crate::message::LapMsg;

/// Decoy lap ordering helper — not linked from lib.rs or the export hot path.
pub fn decoy_merge_lap_order(laps: &[LapMsg]) -> Vec<usize> {
    let mut indexed: Vec<(usize, &LapMsg)> = laps.iter().enumerate().collect();
    indexed.sort_by_key(|(_, lap)| lap.start_time);
    indexed.into_iter().map(|(idx, _)| idx).collect()
}
