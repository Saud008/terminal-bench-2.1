use crate::custody_types::{IntegrityFinding, TransferEvent};

pub fn seal_findings(transfers: &[TransferEvent]) -> Vec<IntegrityFinding> {
    let mut out = Vec::new();
    for row in transfers {
        if row.seal_number != row.expected_seal {
            out.push(IntegrityFinding {
                evidence_id: row.evidence_id.clone(),
                code: "seal_break".into(),
                detail: format!("seal {} expected {}", row.seal_number, row.expected_seal),
            });
        }
    }
    out
}
