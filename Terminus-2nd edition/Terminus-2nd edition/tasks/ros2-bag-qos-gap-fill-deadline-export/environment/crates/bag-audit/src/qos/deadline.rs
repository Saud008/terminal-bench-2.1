use std::collections::BTreeMap;

use crate::model::{BagMetadata, Message};

#[derive(Debug, Clone)]
pub struct DeadlineMiss {
    pub topic: String,
    pub seq: u64,
    pub delta_ns: u64,
    pub deadline_ms: u64,
}

pub fn find_deadline_misses(
    meta: &BagMetadata,
    messages: &[Message],
    speed: f64,
    _seed: u64,
) -> Vec<DeadlineMiss> {
    let mut by_topic: BTreeMap<String, Vec<&Message>> = BTreeMap::new();
    for m in messages {
        by_topic.entry(m.topic.clone()).or_default().push(m);
    }
    let mut misses = Vec::new();
    for (topic, profile) in &meta.topics {
        let Some(rows) = by_topic.get(topic) else {
            continue;
        };
        let mut ordered: Vec<_> = rows.iter().copied().collect();
        ordered.sort_by_key(|m| m.seq);
        let effective_ms = (profile.deadline_ms as f64 * speed) as u64;
        let limit_ns = effective_ms.saturating_mul(1_000_000);
        for pair in ordered.windows(2) {
            let prev = pair[0];
            let cur = pair[1];
            let clock_delta = cur.receive_ns.saturating_sub(prev.receive_ns);
            if profile.deadline_clock == "publish" && clock_delta > limit_ns {
                misses.push(DeadlineMiss {
                    topic: topic.clone(),
                    seq: cur.seq,
                    delta_ns: clock_delta,
                    deadline_ms: profile.deadline_ms,
                });
            }
        }
    }
    misses
}
