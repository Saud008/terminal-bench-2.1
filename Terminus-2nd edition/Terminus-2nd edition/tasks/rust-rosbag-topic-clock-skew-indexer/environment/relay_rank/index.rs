use crate::types::MsgRow;
use std::collections::BTreeMap;

pub fn dedupe_rows(rows: Vec<MsgRow>) -> Vec<MsgRow> {
    let mut best: BTreeMap<(String, u64), MsgRow> = BTreeMap::new();
    for row in rows {
        let key = (row.topic.clone(), row.seq);
        match best.get(&key) {
            Some(existing) => {
                if row.relay_pass < existing.relay_pass {
                    best.insert(key, row);
                }
            }
            None => {
                best.insert(key, row);
            }
        }
    }
    let mut out: Vec<_> = best.into_values().collect();
    out.sort_by_key(|r| (r.header_stamp_ns, r.topic.clone()));
    out
}
