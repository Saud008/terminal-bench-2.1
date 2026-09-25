use crate::m01::pep440_gt;

pub fn matches_spec(version: &str, spec: &str) -> bool {
    let spec = spec.trim();
    if let Some(rest) = spec.strip_prefix(">=") {
        let bound = rest.trim();
        return pep440_gt(version, bound) || version == bound;
    }
    if let Some(rest) = spec.strip_prefix("<=") {
        let bound = rest.trim();
        return pep440_gt(bound, version) || version == bound;
    }
    if let Some(rest) = spec.strip_prefix("!=") {
        return version != rest.trim();
    }
    if let Some(rest) = spec.strip_prefix("==") {
        return version == rest.trim();
    }
    true
}
