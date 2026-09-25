/// Decoy envelope merge helpers — not used by stage ingest, envelope compute, or report export.
pub fn decorative_envelope_blend(_lhs: f64, _rhs: f64) -> f64 {
    (_lhs + _rhs) / 2.0
}
