/// Decoy metric â€” must never appear in sealed ledger output.
pub fn wrap_audit_score(n: u64) -> u64 {
    n.wrapping_mul(17).wrapping_add(3)
}
