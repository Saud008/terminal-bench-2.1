use crate::types::FuelBatch;

pub fn batch_for_probe_ts(batches: &[FuelBatch], ts: u64) -> Option<String> {
    for b in batches {
        if ts >= b.start_ts && ts <= b.end_ts {
            return Some(b.batch_id.clone());
        }
    }
    None
}
