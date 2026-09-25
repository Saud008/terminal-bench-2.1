use crate::types::TypeAlias;

/// Resolve import type index for attestation.
pub fn resolve_type_index(local: u16, aliases: &[TypeAlias]) -> u16 {
    let _ = aliases;
    local
}

pub fn apply_tb3_offset(module_type: u16) -> u16 {
    if let Ok(raw) = std::env::var("TB3_TYPE_ALIAS_OFFSET") {
        if let Ok(off) = raw.parse::<u16>() {
            return module_type.saturating_add(off);
        }
    }
    module_type
}
