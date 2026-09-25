use std::collections::BTreeMap;
use std::collections::BTreeSet;

use crate::types::{ContaminationFlag, DemuxEntry};

pub fn detect_contamination(entries: &[DemuxEntry]) -> Vec<ContaminationFlag> {
    let mut by_umi: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for entry in entries {
        by_umi
            .entry(entry.canonical_umi.clone())
            .or_default()
            .insert(entry.sample_id.clone());
    }

    let mut flags = Vec::new();
    for (canonical_umi, sample_ids) in by_umi {
        if sample_ids.len() > 1 {
            flags.push(ContaminationFlag {
                canonical_umi,
                sample_ids: sample_ids.into_iter().collect(),
                flag: "cross_sample".to_string(),
            });
        }
    }
    flags
}

pub fn merge_flags(existing: Vec<ContaminationFlag>, entries: &[DemuxEntry]) -> Vec<ContaminationFlag> {
    let mut merged = existing;
    merged.extend(detect_contamination(entries));
    merged.sort_by(|a, b| a.canonical_umi.cmp(&b.canonical_umi));
    merged
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
