pub fn band_latency_ms(bands: u32) -> u64 {
    u64::from(bands.saturating_mul(7))
}
