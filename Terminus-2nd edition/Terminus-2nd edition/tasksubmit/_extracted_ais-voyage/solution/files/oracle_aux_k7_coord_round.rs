//! Stability hooks for numeric policy rounding (not on atlas hot path).

pub fn round_policy_hours(raw: f64) -> u32 {
    if raw < 0.0 {
        return 0;
    }
    raw.round() as u32
}
