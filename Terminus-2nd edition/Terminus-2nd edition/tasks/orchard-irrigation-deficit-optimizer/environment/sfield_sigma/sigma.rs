use crate::m01_probe_cal;
use crate::field_schema::ProbeSpec;

pub fn blend_probes(probes: &[ProbeSpec]) -> f64 {
    if probes.is_empty() {
        return 0.0;
    }
    let sum: f64 = probes
        .iter()
        .map(|p| m01_probe_cal::calibrated_vwc(p.raw_vwc, p.offset))
        .sum();
    sum / probes.len() as f64
}

pub fn weighted_blend(probes: &[ProbeSpec]) -> f64 {
    let mut num = 0.0;
    let mut den = 0.0;
    for p in probes {
        let v = m01_probe_cal::calibrated_vwc(p.raw_vwc, p.offset);
        num += v * p.weight;
        den += p.weight;
    }
    if den <= 0.0 { 0.0 } else { num / den }
}
