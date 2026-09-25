/// Decoy crate — not on canonicalize or attestation hot path.
pub fn wrap_score(name: &str) -> u64 {
    name.bytes().map(|b| b as u64).sum()
}
