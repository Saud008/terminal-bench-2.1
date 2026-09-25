use crate::custody_types::{IntegrityFinding, TransferEvent};
use std::collections::HashMap;

pub fn chrono_findings(transfers: &[TransferEvent]) -> Vec<IntegrityFinding> {
    let mut last: HashMap<String, u64> = HashMap::new();
    let mut out = Vec::new();
    let mut ordered: Vec<&TransferEvent> = transfers.iter().collect();
    ordered.sort_by(|a, b| {
        a.evidence_id
            .cmp(&b.evidence_id)
            .then(a.event_epoch_ms.cmp(&b.event_epoch_ms))
            .then(a.event_id.cmp(&b.event_id))
    });
    for row in ordered {
        if let Some(prev) = last.get(&row.evidence_id) {
            if row.event_epoch_ms <= *prev {
                out.push(IntegrityFinding {
                    evidence_id: row.evidence_id.clone(),
                    code: "chronology_violation".into(),
                    detail: format!("{} before {}", row.event_epoch_ms, prev),
                });
            }
        }
        last.insert(row.evidence_id.clone(), row.event_epoch_ms);
    }
    out
}

pub fn lab_window_findings(transfers: &[TransferEvent]) -> Vec<IntegrityFinding> {
    let mut max_transfer: HashMap<String, u64> = HashMap::new();
    for row in transfers {
        if row.event_type == "transfer" {
            let entry = max_transfer.entry(row.evidence_id.clone()).or_insert(0);
            if row.event_epoch_ms > *entry {
                *entry = row.event_epoch_ms;
            }
        }
    }
    let mut out = Vec::new();
    for row in transfers {
        if row.event_type == "lab_submit" {
            let anchor = max_transfer.get(&row.evidence_id).copied().unwrap_or(0);
            if row.event_epoch_ms <= anchor {
                out.push(IntegrityFinding {
                    evidence_id: row.evidence_id.clone(),
                    code: "chronology_violation".into(),
                    detail: "lab_submit before transfer".into(),
                });
            }
        }
    }
    out
}
