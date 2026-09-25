use std::collections::HashMap;

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

/// BROKEN: does not sort fragments, uses raw talker in keys, emits session incompletes.
pub fn compose_stream(
    sentences: Vec<ParsedSentence>,
    mut pending: PendingStore,
    mut rmc_date: Option<String>,
    mut rmc_time: Option<String>,
    use_session: bool,
) -> ComposeResult {
    let mut rejected = Vec::new();
    let mut buckets: HashMap<String, Vec<ParsedSentence>> = HashMap::new();
    let mut order: Vec<String> = Vec::new();
    let mut singles: Vec<MergeGroup> = Vec::new();

    for s in sentences {
        if s.sentence == "RMC" {
            // context update handled outside; still emit as single
        }
        if s.is_multipart {
            let talker = s.talker.clone(); // BROKEN: no canonical
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
            singles.push(MergeGroup {
                merge_key: key,
                talker,
                sentence: s.sentence.clone(),
                multipart_total: 1,
                fragments_merged: 1,
                payload_fields: s.fields.clone(),
                utc_iso: utc,
            });
        }
    }

    let mut groups = Vec::new();
    let mut seen_single = std::collections::HashSet::new();
    for key in &order {
        if let Some(frags) = buckets.remove(key) {
            let combined = if use_session {
                pending.merge_with_pending(key, frags)
            } else {
                frags
            };
            pending.finalize_bucket(key.clone(), combined, use_session, &mut groups);
        } else if let Some(g) = singles.iter().find(|g| &g.merge_key == key) {
            if seen_single.insert(g.merge_key.clone()) {
                groups.push(g.clone());
            }
        }
    }
    for g in singles {
        if seen_single.insert(g.merge_key.clone()) {
            groups.push(g);
        }
    }

    let _ = (&mut rmc_date, &mut rmc_time, &mut rejected);
    ComposeResult {
        groups,
        rejected,
        rmc_date,
        rmc_time,
        pending,
    }
}
