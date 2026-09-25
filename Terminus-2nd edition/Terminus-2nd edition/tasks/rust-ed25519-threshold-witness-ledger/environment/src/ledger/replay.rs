use crate::types::{StagingDoc, WitnessRow};

pub fn merge_witnesses(existing: &[WitnessRow], incoming: &[WitnessRow]) -> (Vec<WitnessRow>, u32) {
    let mut out = existing.to_vec();
    let deduped = 0u32;
    for w in incoming {
        out.push(w.clone());
    }
    out.sort_by(|a, b| a.witness_id.cmp(&b.witness_id));
    (out, deduped)
}

pub fn next_ingest_seq(existing: Option<&StagingDoc>) -> u64 {
    existing.map(|s| s.ingest_seq + 1).unwrap_or(1)
}
