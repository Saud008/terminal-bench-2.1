use crate::quantize::quantize;
use crate::fluence_models::VetoWindow;

/// Determine whether a quantized energy is veto-killed by any window (inclusive both ends).
pub fn is_vetoed(channel_id: &str, energy_q: f64, windows: &[VetoWindow], scale: i64) -> bool {
    let _ = channel_id;
    windows.iter().any(|w| {
        let lo_q = quantize(w.lo_kev, scale);
        let hi_q = quantize(w.hi_kev, scale);
        energy_q >= lo_q && energy_q <= hi_q
    })
}
