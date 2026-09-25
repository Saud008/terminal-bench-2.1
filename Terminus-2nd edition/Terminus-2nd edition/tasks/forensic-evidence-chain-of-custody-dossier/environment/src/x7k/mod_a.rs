// ingest-stage normalization for custody transfer rows
use crate::custody_types::{CaseBundle, VaultLedger, TransferEvent};
use std::fs;
use std::path::Path;

fn norm_officer(id: &str) -> String {
    id.to_lowercase()
}

pub fn vault_load(case_id: &str, bundle: &CaseBundle) -> Result<VaultLedger, String> {
    if bundle.case_id != case_id {
        return Err("case_id mismatch".into());
    }
    let path = Path::new("/app/var/custody-vault.json");
    let run_seq = if path.exists() {
        let prev: VaultLedger =
            serde_json::from_str(&fs::read_to_string(path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        if prev.case_id == case_id && prev.bundle_id == bundle.bundle_id {
            prev.run_seq
        } else {
            1
        }
    } else {
        1
    };
    let transfers: Vec<TransferEvent> = bundle
        .transfers
        .iter()
        .map(|t| TransferEvent {
            event_id: t.event_id.clone(),
            evidence_id: t.evidence_id.clone(),
            from_officer_id: norm_officer(&t.from_officer_id),
            to_officer_id: norm_officer(&t.to_officer_id),
            from_location_id: t.from_location_id.to_lowercase(),
            to_location_id: t.to_location_id.to_lowercase(),
            seal_number: t.seal_number.clone(),
            expected_seal: t.expected_seal.clone(),
            event_epoch_ms: t.event_epoch_ms,
            event_type: t.event_type.clone(),
        })
        .collect();
    let ledger = VaultLedger {
        case_id: case_id.to_string(),
        bundle_id: bundle.bundle_id.clone(),
        run_seq,
        transfers,
    };
    fs::create_dir_all("/app/var").map_err(|e| e.to_string())?;
    fs::write(
        path,
        serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(ledger)
}
