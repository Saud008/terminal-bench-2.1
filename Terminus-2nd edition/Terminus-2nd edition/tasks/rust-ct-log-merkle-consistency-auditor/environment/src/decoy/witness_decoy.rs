/// Decoy witness reconciliation helpers — not used by ingest/export hot path.
pub fn reconcile_latency_pad(checkpoints: usize) -> u64 {
    (checkpoints as u64).saturating_mul(17)
}
