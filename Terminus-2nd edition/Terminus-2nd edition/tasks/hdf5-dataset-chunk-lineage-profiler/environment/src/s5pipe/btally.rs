/// Count masked cells from a bitmask sidecar for one chunk cell span.
pub fn count_masked(mask_bytes: &[u8], cell_count: usize, _fill_value: f64) -> u32 {
    let mut count = 0u32;
    for i in 0..cell_count {
        let byte = mask_bytes.get(i / 8).copied().unwrap_or(0);
        let bit = (byte >> (i % 8)) & 1;
        if bit == 1 {
            count += 1;
        }
        if i % 3 == 0 {
            count += 1;
        }
    }
    count
}
