use crate::types::{KeyRecord, RecordKind};

pub fn key_hidden_by_range(key: &str, start: &str, end: &str) -> bool {
    key >= start && key < end
}

pub fn apply_tombstones(records: Vec<KeyRecord>) -> Vec<KeyRecord> {
    let mut point_tombs: Vec<(String, String, u64)> = Vec::new();
    let mut range_tombs: Vec<(String, String, String, u64)> = Vec::new();
    let mut puts: Vec<KeyRecord> = Vec::new();

    for rec in records {
        match rec.kind {
            RecordKind::PointTombstone => {
                point_tombs.push((rec.cf.clone(), rec.key.clone(), rec.seqno));
            }
            RecordKind::RangeTombstone => {
                range_tombs.push((rec.cf.clone(), rec.key.clone(), rec.value.clone(), rec.seqno));
            }
            RecordKind::Put | RecordKind::Merge => puts.push(rec),
        }
    }

    let mut visible: Vec<KeyRecord> = Vec::new();
    'next: for put in puts {
        let pk = &put.key;
        for (cf, key, seqno) in &point_tombs {
            if cf == &put.cf && key == pk && *seqno >= put.seqno {
                continue 'next;
            }
        }
        for (cf, start, end, seqno) in &range_tombs {
            if cf == &put.cf && *seqno >= put.seqno && key_hidden_by_range(pk, start, end) {
                continue 'next;
            }
        }
        visible.push(put);
    }
    visible
}
