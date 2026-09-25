use crate::types::StagedRecord;

pub fn pick_winner<'a>(a: &'a StagedRecord, b: &'a StagedRecord) -> &'a StagedRecord {
    if a.feed_id <= b.feed_id {
        a
    } else {
        b
    }
}

pub fn resolve_records(records: &[StagedRecord]) -> Vec<StagedRecord> {
    let mut keys: Vec<String> = records.iter().map(|r| r.cidr.clone()).collect();
    keys.sort();
    keys.dedup();
    let mut out = Vec::new();
    for key in keys {
        let group: Vec<&StagedRecord> = records.iter().filter(|r| r.cidr == key).collect();
        if group.is_empty() {
            continue;
        }
        let mut winner = group[0];
        for cand in &group[1..] {
            winner = pick_winner(winner, cand);
        }
        out.push(winner.clone());
    }
    out.sort_by(|a, b| a.cidr.cmp(&b.cidr));
    out
}
