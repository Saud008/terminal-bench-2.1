pub fn raw_to_norm_ns(ts_sec: u32, ts_usec: u32) -> u64 {
    (ts_sec as u64) * 1_000_000_000 + ts_usec as u64
}

pub fn compute_norm_from_raw(raw_ts_us: u64) -> u64 {
    raw_ts_us * 1000
}
