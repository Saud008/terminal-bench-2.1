pub fn unified_azimuth_centideg(raw: u32, prev_raw: Option<u32>) -> u32 {
    let mut unified = raw;
    if let Some(prev) = prev_raw {
        if raw < prev {
            unified = raw.saturating_add(36000);
        }
    }
    unified
}

pub fn azimuth_span_centideg(unified: &[u32]) -> u32 {
    if unified.is_empty() {
        return 0;
    }
    let min = *unified.iter().min().unwrap();
    let max = *unified.iter().max().unwrap();
    max.saturating_sub(min)
}
