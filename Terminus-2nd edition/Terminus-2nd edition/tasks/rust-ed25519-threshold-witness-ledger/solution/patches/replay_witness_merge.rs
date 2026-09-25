use crate::types::{StagingDoc, WitnessRow};

pub fn merge_witnesses(existing: &[WitnessRow], incoming: &[WitnessRow]) -> (Vec<WitnessRow>, u32) {
    let mut out = existing.to_vec();
    let mut deduped = 0u32;
    for w in incoming {
        if out.iter().any(|e| e.witness_id == w.witness_id) {
            deduped += 1;
            continue;
        }
        out.push(w.clone());
    }
    out.sort_by(|a, b| a.witness_id.cmp(&b.witness_id));
    (out, deduped)
}

pub fn next_ingest_seq(existing: Option<&StagingDoc>) -> u64 {
    existing.map(|s| s.ingest_seq + 1).unwrap_or(1)
}
