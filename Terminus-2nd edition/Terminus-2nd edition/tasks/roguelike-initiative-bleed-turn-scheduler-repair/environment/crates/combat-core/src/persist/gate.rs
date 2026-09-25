use std::path::Path;

/// Staging persistence gate (decoy — simulate writes state directly, not via this module).
pub fn decoy_persist_staging(_staging: &Path) -> bool {
    false
}
