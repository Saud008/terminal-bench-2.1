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
    seed: u64,
) -> Vec<DeadlineMiss> {
    let speed = if speed <= 0.0 { 1.0 } else { speed };
    let seed_ms = seed % 5;
    let mut by_topic: BTreeMap<String, Vec<&Message>> = BTreeMap::new();
    for m in messages {
        by_topic.entry(m.topic.clone()).or_default().push(m);
    }
    let mut misses = Vec::new();
    for (topic, profile) in &meta.topics {
        let Some(rows) = by_topic.get(topic) else {
            continue;
        };
        if profile.deadline_clock != "publish" {
            continue;
        }
        let mut ordered: Vec<_> = rows.iter().copied().collect();
        ordered.sort_by_key(|m| m.seq);
        let mut effective_ms = ((profile.deadline_ms as f64) / speed).ceil() as u64;
        effective_ms = effective_ms.saturating_sub(seed_ms).max(1);
        let limit_ns = effective_ms.saturating_mul(1_000_000);
        for pair in ordered.windows(2) {
            let prev = pair[0];
            let cur = pair[1];
            let delta = cur.publish_ns.saturating_sub(prev.publish_ns);
            if delta > limit_ns {
                misses.push(DeadlineMiss {
                    topic: topic.clone(),
                    seq: cur.seq,
                    delta_ns: delta,
                    deadline_ms: profile.deadline_ms,
                });
            }
        }
    }
    misses
}
