use std::collections::BTreeMap;

use crate::model::Message;

pub fn fill_gaps(messages: Vec<Message>, _seed: u64) -> Vec<Message> {
    let mut by_topic: BTreeMap<String, Vec<Message>> = BTreeMap::new();
    for m in messages {
        by_topic.entry(m.topic.clone()).or_default().push(m);
    }
    let mut out = Vec::new();
    for (_topic, mut rows) in by_topic {
        rows.sort_by_key(|m| m.seq);
        if rows.is_empty() {
            continue;
        }
        let min_seq = rows.first().unwrap().seq;
        let max_seq = rows.last().unwrap().seq;
        for seq in min_seq..=max_seq {
            if let Some(existing) = rows.iter().find(|r| r.seq == seq) {
                out.push(existing.clone());
                continue;
            }
            let next = rows.iter().find(|r| r.seq > seq);
            let prev = rows.iter().filter(|r| r.seq < seq).last();
            let publish_ns = interpolate_publish(seq, prev, next);
            let payload = Vec::new();
            out.push(Message {
                topic: rows[0].topic.clone(),
                seq,
                publish_ns,
                receive_ns: publish_ns,
                payload,
                synthetic: true,
            });
        }
    }
    out.sort_by(|a, b| (a.topic.clone(), a.seq).cmp(&(b.topic.clone(), b.seq)));
    out
}

fn interpolate_publish(seq: u64, prev: Option<&Message>, next: Option<&Message>) -> u64 {
    match (prev, next) {
        (Some(p), Some(n)) if n.seq > p.seq => {
            let steps = n.seq - p.seq;
            let pos = seq - p.seq;
            let span = n.publish_ns.saturating_sub(p.publish_ns);
            p.publish_ns + (span * pos) / steps
        }
        (Some(p), None) => p.publish_ns.saturating_add(seq.saturating_sub(p.seq)),
        (None, Some(n)) => n.publish_ns.saturating_sub(n.seq.saturating_sub(seq)),
        _ => 0,
    }
}
