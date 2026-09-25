use crate::custody_types::{IntegrityFinding, TransferEvent};
use std::collections::HashMap;

pub fn chrono_findings(transfers: &[TransferEvent]) -> Vec<IntegrityFinding> {
    let mut last: HashMap<String, u64> = HashMap::new();
    let mut out = Vec::new();
    for row in transfers {
        let prev = last.get(&row.evidence_id).copied().unwrap_or(0);
        if row.event_epoch_ms < prev {
            out.push(IntegrityFinding {
                evidence_id: row.evidence_id.clone(),
                code: "chronology_violation".into(),
                detail: format!("{} before {}", row.event_epoch_ms, prev),
            });
        }
        last.insert(row.evidence_id.clone(), row.event_epoch_ms);
    }
    out
}

pub fn lab_window_findings(transfers: &[TransferEvent]) -> Vec<IntegrityFinding> {
    let mut last_transfer: HashMap<String, u64> = HashMap::new();
    let mut out = Vec::new();
    for row in transfers {
        if row.event_type == "transfer" {
            last_transfer.insert(row.evidence_id.clone(), row.event_epoch_ms);
        }
        if row.event_type == "lab_submit" {
            let anchor = last_transfer.get(&row.evidence_id).copied().unwrap_or(0);
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
