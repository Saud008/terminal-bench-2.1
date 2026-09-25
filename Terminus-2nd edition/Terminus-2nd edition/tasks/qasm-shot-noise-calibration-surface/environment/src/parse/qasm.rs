/// QASM decorative parse helpers — not used by stage ingest hot path.
pub fn decorative_gate_weight(line: &str) -> f64 {
    if line.trim().ends_with(';') {
        1.0
    } else {
        0.0
    }
}
