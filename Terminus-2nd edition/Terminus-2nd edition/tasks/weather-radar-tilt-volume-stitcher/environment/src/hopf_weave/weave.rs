pub fn unified_azimuth_centideg(raw: u32) -> u32 {
    raw
}

pub fn azimuth_span_centideg(azimuths: &[u32]) -> u32 {
    if azimuths.is_empty() {
        return 0;
    }
    let min = *azimuths.iter().min().unwrap();
    let max = *azimuths.iter().max().unwrap();
    max.saturating_sub(min)
}
