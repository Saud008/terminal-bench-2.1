use crate::feed_reader::kind_tag;
use crate::route_model::FeedEvent;

pub fn assert_peer_monotonic(events: &[FeedEvent]) -> Result<(), String> {
    let mut last: std::collections::HashMap<String, u64> = std::collections::HashMap::new();
    for ev in events {
        if let Some(prev) = last.get(&ev.peer) {
            if ev.ts_ms < *prev {
                return Err(format!("peer {} ts regression", ev.peer));
            }
        }
        last.insert(ev.peer.clone(), ev.ts_ms);
    }
    Ok(())
}

pub fn dedupe(events: Vec<FeedEvent>) -> Vec<FeedEvent> {
    let mut seen = std::collections::HashSet::new();
    let mut out = Vec::new();
    for ev in events {
        let key = (ev.ts_ms, ev.peer.clone(), ev.prefix.clone(), kind_tag(&ev.kind));
        if seen.insert(key) {
            out.push(ev);
        }
    }
    out
}

pub fn sort_feed(events: &mut [FeedEvent]) {
    events.sort_by(|a, b| {
        a.ts_ms
            .cmp(&b.ts_ms)
            .then_with(|| a.peer.cmp(&b.peer))
            .then_with(|| a.prefix.cmp(&b.prefix))
            .then_with(|| kind_tag(&a.kind).cmp(&kind_tag(&b.kind)))
    });
}
