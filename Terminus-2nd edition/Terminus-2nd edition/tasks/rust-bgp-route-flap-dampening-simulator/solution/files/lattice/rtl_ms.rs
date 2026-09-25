pub fn ms_to_reuse(penalty_now: u64, reuse_threshold: u64, half_life_ms: u64) -> Result<u64, String> {
    if half_life_ms == 0 {
        return Err("half_life_ms must be non-zero".into());
    }
    if penalty_now < reuse_threshold {
        return Ok(0);
    }
    // Integer-only decay: penalty' = floor(penalty * half_life_ms / (half_life_ms + delta)).
    // Find minimal delta such that floor(penalty_now * half_life_ms / (half_life_ms + delta)) < reuse_threshold.
    let mut lo: u64 = 0;
    let mut hi: u64 = half_life_ms.saturating_mul(penalty_now).saturating_add(1).max(1);
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        let next = penalty_now.saturating_mul(half_life_ms) / (half_life_ms + mid);
        if next < reuse_threshold {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    Ok(lo)
}
