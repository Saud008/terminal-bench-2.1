use std::collections::{HashMap, HashSet};

use crate::merge::{datetime, multipart};
use crate::model::{MergeGroup, ParsedSentence, RejectedLine};
use crate::session::pending::PendingStore;
use crate::talker::normalize;

pub struct ComposeResult {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub rmc_date: Option<String>,
    pub rmc_time: Option<String>,
    pub pending: PendingStore,
}

pub fn compose_stream(
    sentences: Vec<ParsedSentence>,
    mut pending: PendingStore,
    rmc_date: Option<String>,
    rmc_time: Option<String>,
    use_session: bool,
) -> ComposeResult {
    let mut buckets: HashMap<String, Vec<ParsedSentence>> = HashMap::new();
    let mut order: Vec<String> = Vec::new();
    let mut single_map: HashMap<String, MergeGroup> = HashMap::new();

    for s in sentences {
        if s.is_multipart {
            let talker = normalize::canonical_talker(&s.talker);
            let total = s.fields.first().and_then(|v| v.parse().ok()).unwrap_or(1);
            let key = multipart::merge_key(&talker, &s.sentence, total);
            if !buckets.contains_key(&key) {
                order.push(key.clone());
                let prior = pending.take_fragments(&key);
                buckets.insert(key.clone(), prior);
            }
            buckets.get_mut(&key).unwrap().push(s);
        } else {
            let talker = normalize::canonical_talker(&s.talker);
            let key = format!("{talker}:{}:1", s.sentence);
            let utc = s.fields.first().and_then(|t| {
                datetime::attach_utc(rmc_date.as_deref(), rmc_time.as_deref(), t)
            });
            if !order.contains(&key) {
                order.push(key.clone());
            }
            single_map.insert(
                key.clone(),
                MergeGroup {
                    merge_key: key,
                    talker,
                    sentence: s.sentence.clone(),
                    multipart_total: 1,
                    fragments_merged: 1,
                    payload_fields: s.fields.clone(),
                    utc_iso: utc,
                },
            );
        }
    }

    let mut groups = Vec::new();
    let mut emitted = HashSet::new();
    for key in &order {
        if let Some(frags) = buckets.remove(key) {
            let combined = pending.merge_with_pending(key, frags);
            pending.finalize_bucket(key.clone(), combined, use_session, &mut groups);
            emitted.insert(key.clone());
        } else if let Some(g) = single_map.get(key) {
            groups.push(g.clone());
            emitted.insert(key.clone());
        }
    }

    ComposeResult {
        groups,
        rejected: Vec::new(),
        rmc_date,
        rmc_time,
        pending,
    }
}
