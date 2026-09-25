use crate::types::TempoEvent;

pub fn tick_to_seconds(tick: u64, ppq: u32, events: &[TempoEvent]) -> f64 {
    if tick == 0 || events.is_empty() {
        return 0.0;
    }
    let mut ordered = events.to_vec();
    ordered.sort_by_key(|e| e.tick);
    let mut sec = 0.0;
    for i in 0..ordered.len() {
        let start = ordered[i].tick;
        if tick <= start {
            break;
        }
        let end = if i + 1 < ordered.len() {
            ordered[i + 1].tick
        } else {
            tick
        };
        let clip = tick.min(end);
        let delta = clip.saturating_sub(start);
        if delta > 0 {
            sec += (delta as f64 / ppq as f64)
                * (ordered[i].microseconds_per_quarter as f64 / 1_000_000.0);
        }
        if tick <= end {
            break;
        }
    }
    sec
}
