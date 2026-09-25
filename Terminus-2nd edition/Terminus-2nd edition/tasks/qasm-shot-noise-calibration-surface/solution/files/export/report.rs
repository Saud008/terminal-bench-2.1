use std::fs;

use sha2::{Digest, Sha256};

use crate::staging;
use crate::types::{EnvelopeExport, QubitEnvelope};

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

    let normalized: EnvelopeExport = serde_json::from_str(&pretty).map_err(|e| e.to_string())?;
    let bytes = canonical_digest_bytes(&normalized)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    fs::write(digest_path, format!("{digest}\n")).map_err(|e| e.to_string())
}

fn canonical_digest_bytes(export: &EnvelopeExport) -> Result<Vec<u8>, String> {
    Ok(canonical_digest_json(export)?.into_bytes())
}

fn canonical_digest_json(export: &EnvelopeExport) -> Result<String, String> {
    let mut keys: Vec<_> = export.envelopes.keys().cloned().collect();
    keys.sort();

    let mut envelope_parts = Vec::new();
    for key in keys {
        let env = &export.envelopes[&key];
        envelope_parts.push(format!(
            "{}:{}",
            serde_json::to_string(&key).map_err(|e| e.to_string())?,
            envelope_json(env)?
        ));
    }

    let chain = serde_json::to_string(&export.provenance.chain).map_err(|e| e.to_string())?;
    let provenance = format!(
        r#"{{"chain":{},"digest":"{}"}}"#,
        chain, export.provenance.digest
    );

    Ok(format!(
        r#"{{"experiment_id":"{}","selected_matrix_id":"{}","envelopes":{{{}}},"provenance":{}}}"#,
        export.experiment_id,
        export.selected_matrix_id,
        envelope_parts.join(","),
        provenance
    ))
}

fn envelope_json(env: &QubitEnvelope) -> Result<String, String> {
    let mitigated = serde_json::to_string(&env.mitigated).map_err(|e| e.to_string())?;
    let intervals = serde_json::to_string(&env.intervals).map_err(|e| e.to_string())?;
    Ok(format!(
        r#"{{"mitigated":{},"intervals":{},"total_shots":{}}}"#,
        mitigated, intervals, env.total_shots
    ))
}
