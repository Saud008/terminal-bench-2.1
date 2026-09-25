use crate::countersign_order::unwind_chain;
use crate::errors::AuditError;
use crate::ledger::Ledger;
use crate::model::ChainResult;
use serde_json::json;
use std::fs;
use std::path::Path;

pub fn export_manifest(
    ledger: &Ledger,
    manifest_path: &str,
) -> Result<usize, AuditError> {
    let rows = ledger.all_rows()?;
    if rows.is_empty() {
        return Err(AuditError::EmptyLedger);
    }
    let mut chains = vec![];
    for row in rows {
        let sign1 = crate::model::parse_sign1(&row.cose_bytes)
            .map_err(|e| AuditError::Parse(e))?;
        let (outer_ok, countersign_ok, unwind) = unwind_chain(&sign1)
            .map_err(|e| AuditError::Parse(e))?;
        if !(outer_ok && countersign_ok) {
            continue;
        }
        chains.push(ChainResult {
            input_sha256: row.sha256.clone(),
            outer_ok,
            countersign_ok,
            partial_retained: outer_ok && !countersign_ok,
            unwind,
        });
    }
    let body = json!({
        "ledger_rows": chains.len(),
        "chains": chains,
    });
    if let Some(parent) = Path::new(manifest_path).parent() {
        fs::create_dir_all(parent).map_err(|e| AuditError::Io(e.to_string()))?;
    }
    let text = serde_json::to_string_pretty(&body).map_err(|e| AuditError::Parse(e.to_string()))?;
    fs::write(manifest_path, format!("{text}\n")).map_err(|e| AuditError::Io(e.to_string()))?;
    Ok(chains.len())
}
