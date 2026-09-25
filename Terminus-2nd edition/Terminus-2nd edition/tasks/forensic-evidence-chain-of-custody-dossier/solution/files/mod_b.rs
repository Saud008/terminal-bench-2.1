use crate::custody_types::{LineageEdge, TransferEvent};

pub fn build_edges(transfers: &[TransferEvent]) -> Vec<LineageEdge> {
    let mut rows: Vec<&TransferEvent> = transfers
        .iter()
        .filter(|t| t.event_type == "transfer")
        .collect();
    rows.sort_by(|a, b| {
        a.evidence_id
            .cmp(&b.evidence_id)
            .then(a.event_epoch_ms.cmp(&b.event_epoch_ms))
            .then(a.event_id.cmp(&b.event_id))
    });
    rows.into_iter()
        .map(|t| LineageEdge {
            evidence_id: t.evidence_id.clone(),
            from_officer_id: t.from_officer_id.clone(),
            to_officer_id: t.to_officer_id.clone(),
            event_epoch_ms: t.event_epoch_ms,
        })
        .collect()
}

pub fn lineage_gap(evidence_id: &str, transfers: &[TransferEvent]) -> bool {
    let mut chain: Vec<&TransferEvent> = transfers
        .iter()
        .filter(|t| t.evidence_id == evidence_id && t.event_type == "transfer")
        .collect();
    chain.sort_by_key(|t| t.event_epoch_ms);
    if chain.len() < 2 {
        return false;
    }
    for w in chain.windows(2) {
        if w[0].to_officer_id != w[1].from_officer_id {
            return true;
        }
    }
    false
}
