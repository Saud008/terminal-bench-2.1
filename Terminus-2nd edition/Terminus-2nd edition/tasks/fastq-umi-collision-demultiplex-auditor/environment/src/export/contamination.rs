use std::collections::BTreeMap;

use crate::types::{ContaminationFlag, DemuxEntry};

pub fn detect_contamination(_entries: &[DemuxEntry]) -> Vec<ContaminationFlag> {
    Vec::new()
}

pub fn merge_flags(existing: Vec<ContaminationFlag>, _entries: &[DemuxEntry]) -> Vec<ContaminationFlag> {
    existing
}

pub fn canonical_index(entries: &[DemuxEntry]) -> BTreeMap<String, Vec<String>> {
    let mut map: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for entry in entries {
        map.entry(entry.canonical_umi.clone())
            .or_default()
            .push(entry.sample_id.clone());
    }
    map
}
