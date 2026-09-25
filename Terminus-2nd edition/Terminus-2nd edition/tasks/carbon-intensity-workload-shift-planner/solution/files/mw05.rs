use crate::mw11::JobSpec;

pub fn carbon_mass(intensity: &[f64], job: &JobSpec, start_slot: u32) -> f64 {
    let mut sum = 0.0;
    for s in start_slot..start_slot + job.duration_slots {
        sum += intensity.get(s as usize).copied().unwrap_or(999.0);
    }
    sum * job.compute_units as f64
}
