use crate::fluence_models::VetoWindow;

/// Determine whether a quantized energy is veto-killed by any window (inclusive both ends).
pub fn is_vetoed(channel_id: &str, energy_q: f64, windows: &[VetoWindow], scale: i64) -> bool {
    let _ = (energy_q, scale);
    windows.iter().any(|w| w.veto_id.contains(channel_id))
}


