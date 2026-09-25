use crate::types::LossEvent;
use std::collections::BTreeMap;

pub fn suppress_duplicates(events: Vec<LossEvent>, tolerance_m: f64) -> (Vec<LossEvent>, u32) {
    let mut buckets: BTreeMap<i64, LossEvent> = BTreeMap::new();
    let mut suppressed = 0u32;
    for ev in events {
        let bucket = (ev.distance_m / tolerance_m) as i64;
        match buckets.get(&bucket) {
            Some(existing) => {
                suppressed += 1;
                if ev.epoch < existing.epoch {
                    buckets.insert(bucket, ev);
                }
            }
            None => {
                buckets.insert(bucket, ev);
            }
        }
    }
    let mut out: Vec<_> = buckets.into_values().collect();
    out.sort_by(|a, b| a.distance_m.partial_cmp(&b.distance_m).unwrap());
    (out, suppressed)
}
