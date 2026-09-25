use crate::errors::AuditError;
use crate::ledger::Ledger;
use crate::staging::{parse_for_staging, sha256_file, write_staging};
use sha2::{Digest, Sha256};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

pub fn resolve_input(input: &str) -> Result<PathBuf, AuditError> {
    if let Ok(base) = env::var("TB3_COSE_DIR") {
        if Path::new(&base).is_absolute() {
            let name = Path::new(input)
                .file_name()
                .and_then(|s| s.to_str())
                .ok_or_else(|| AuditError::Parse("input must be basename with TB3_COSE_DIR".into()))?;
            return Ok(PathBuf::from(base).join(name));
        }
    }
    Ok(PathBuf::from(input))
}

pub fn run_ingest(input: &str, ledger_path: &str, staging_path: &str) -> Result<(), AuditError> {
    let resolved = resolve_input(input)?;
    let bytes = fs::read(&resolved).map_err(|e| AuditError::Io(e.to_string()))?;
    let sign1 = parse_for_staging(&bytes).map_err(|e| AuditError::Parse(e))?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let ledger = Ledger::open(ledger_path)?;
    ledger.upsert(&sha, &bytes)?;
    write_staging(
        staging_path,
        resolved.to_str().ok_or_else(|| AuditError::Parse("path utf8".into()))?,
        &sign1,
    )
    .map_err(|e| AuditError::Parse(e))?;
    Ok(())
}

pub fn sha256_of_resolved(input: &str) -> Result<String, AuditError> {
    let resolved = resolve_input(input)?;
    sha256_file(resolved.to_str().unwrap()).map_err(|e| AuditError::Io(e))
}
