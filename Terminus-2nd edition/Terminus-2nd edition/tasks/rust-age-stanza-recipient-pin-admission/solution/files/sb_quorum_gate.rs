use crate::parse::header_scan::ParsedFile;
use crate::policy::pin_set::PinPolicy;
use std::collections::BTreeSet;

pub fn matched_pin_count(file: &ParsedFile, policy: &PinPolicy) -> usize {
    let mut set = BTreeSet::new();
    for st in &file.stanzas {
        if policy.pins.contains(&st.fingerprint) {
            set.insert(st.fingerprint.clone());
        }
    }
    set.len()
}

pub fn quorum_satisfied(file: &ParsedFile, policy: &PinPolicy) -> bool {
    matched_pin_count(file, policy) >= policy.quorum_k
}
