pub fn apply_decay(penalty: u64, last_ts_ms: u64, now_ms: u64, half_life_ms: u64) -> u64 {
    if now_ms <= last_ts_ms || half_life_ms == 0 {
        return penalty;
    }
    let delta = now_ms - last_ts_ms;
    let factor = 0.5_f64.powf(delta as f64 / half_life_ms as f64);
    ((penalty as f64) * factor).floor() as u64
}
