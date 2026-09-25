pub fn kc_for_stage(stages: &[f64], crop_stage: u32) -> f64 {
    let idx = crop_stage as usize;
    if stages.is_empty() {
        return 1.0;
    }
    *stages.get(idx).unwrap_or_else(|| stages.last().unwrap())
}
