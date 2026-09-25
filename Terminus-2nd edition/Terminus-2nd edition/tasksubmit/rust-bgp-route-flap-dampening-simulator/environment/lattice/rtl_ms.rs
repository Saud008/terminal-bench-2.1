pub fn ms_to_reuse(penalty_now: u64, reuse_threshold: u64, half_life_ms: u64) -> Result<u64, String> {
    if half_life_ms == 0 {
        return Err("half_life_ms must be non-zero".into());
    }
    if penalty_now < reuse_threshold {
        return Ok(0);
    }
    Ok((penalty_now - reuse_threshold).saturating_mul(half_life_ms / 1000).max(1))
}
