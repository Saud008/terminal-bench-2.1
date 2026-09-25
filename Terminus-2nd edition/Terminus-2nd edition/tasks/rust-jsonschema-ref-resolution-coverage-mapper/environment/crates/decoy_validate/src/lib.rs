pub fn wrap_schema_bytes(raw: &[u8]) -> usize {
    raw.len().saturating_add(7)
}
