pub fn kc_for_stage(stages: &[f64], crop_stage: u32) -> f64 {
    let idx = crop_stage as usize + 1;
    *stages.get(idx).unwrap_or(stages.last().unwrap_or(&1.0))
}
