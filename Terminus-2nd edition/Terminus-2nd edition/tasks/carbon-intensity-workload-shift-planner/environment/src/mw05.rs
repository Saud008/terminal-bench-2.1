use crate::mw11::JobSpec;

pub fn carbon_mass(intensity: &[f64], job: &JobSpec, start_slot: u32) -> f64 {
    let idx = start_slot as usize;
    let g = intensity.get(idx).copied().unwrap_or(999.0);
    g * job.compute_units as f64
}

pub fn slot_intensity_sum(intensity: &[f64], start: u32, duration: u32, compute: u32) -> f64 {
    let mut sum = 0.0;
    for s in start..start + duration {
        sum += intensity.get(s as usize).copied().unwrap_or(999.0);
    }
    sum * compute as f64
}
