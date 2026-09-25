use std::fs;

use sha2::{Digest, Sha256};

use crate::staging;
use crate::types::EnvelopeExport;

pub fn export_report(
    ledger_path: &str,
    envelope_path: &str,
    digest_path: &str,
) -> Result<(), String> {
    let ledger = staging::load_ledger(ledger_path)?;

    let export = EnvelopeExport {
        experiment_id: ledger.experiment_id.clone(),
        selected_matrix_id: ledger.selected_matrix_id.clone(),
        envelopes: ledger.envelopes.clone(),
        provenance: ledger.provenance.clone(),
    };

    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&export).map_err(|e| e.to_string())?;
    fs::write(envelope_path, format!("{pretty}\n")).map_err(|e| e.to_string())?;

    let digest_payload = serde_json::json!({
        "experiment_id": export.experiment_id,
        "selected_matrix_id": export.selected_matrix_id,
        "envelopes": export.envelopes,
    });
    let bytes = serde_json::to_vec(&digest_payload).map_err(|e| e.to_string())?;
    let digest = hex::encode(Sha256::digest(bytes));
    fs::write(digest_path, format!("{digest}\n")).map_err(|e| e.to_string())
}
