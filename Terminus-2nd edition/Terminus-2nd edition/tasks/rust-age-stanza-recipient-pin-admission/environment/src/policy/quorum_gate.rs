use crate::parse::header_scan::ParsedFile;
use crate::policy::pin_set::PinPolicy;

pub fn matched_pin_count(file: &ParsedFile, policy: &PinPolicy) -> usize {
    file.stanzas
        .iter()
        .filter(|s| policy.pins.contains(&s.fingerprint))
        .count()
}

pub fn quorum_satisfied(file: &ParsedFile, policy: &PinPolicy) -> bool {
    matched_pin_count(file, policy) >= policy.quorum_k
}
