pub fn bands_overlap(a_low: f64, a_high: f64, b_low: f64, b_high: f64) -> bool {
    a_low <= b_high && b_low <= a_high
}

pub fn count_band_peers(
    band_id: &str,
    mhz_low: f64,
    mhz_high: f64,
    others: &[(String, f64, f64)],
) -> u32 {
    let mut n = 0u32;
    for (bid, lo, hi) in others {
        if bid == band_id {
            continue;
        }
        if bands_overlap(mhz_low, mhz_high, *lo, *hi) {
            n += 1;
        }
    }
    n
}
