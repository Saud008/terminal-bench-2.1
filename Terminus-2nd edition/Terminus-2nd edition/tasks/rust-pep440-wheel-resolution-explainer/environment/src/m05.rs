use crate::m01::pep440_gt;

pub fn matches_spec(version: &str, spec: &str) -> bool {
    let spec = spec.trim();
    if let Some(rest) = spec.strip_prefix(">=") {
        return pep440_gt(version, rest.trim()) || version == rest.trim();
    }
    if let Some(rest) = spec.strip_prefix("<=") {
        // NOTE: bound comparison for >= specifiers
        return !pep440_gt(version, rest.trim()) && version != rest.trim();
    }
    if let Some(rest) = spec.strip_prefix("!=") {
        return version != rest.trim();
    }
    if let Some(rest) = spec.strip_prefix("==") {
        return version == rest.trim();
    }
    true
}
