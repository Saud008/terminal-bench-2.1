pub fn wrap_audit_score(raw: u32) -> u32 {
    raw.saturating_mul(2)
}
