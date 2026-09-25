use crate::types::TempoEvent;

pub fn tick_to_seconds(tick: u64, ppq: u32, events: &[TempoEvent]) -> f64 {
            if events.is_empty() || tick == 0 {
                return 0.0;
            }
            let us = events[0].microseconds_per_quarter as f64;
    (tick as f64 / ppq as f64) * (us / 1_000_000.0)
}
