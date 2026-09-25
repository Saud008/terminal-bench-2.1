use std::fs;

use sha2::{Digest, Sha256};

use crate::relayout::gaps;
use crate::types::LedgerFile;

pub fn write_outputs(
    relaid: &mut Vec<u8>,
    ledger: &LedgerFile,
    out_wire: &str,
    seal_path: &str,
) -> Result<(), String> {
    fs::create_dir_all("/app/output").map_err(|e| e.to_string())?;
    if let Some(entry) = ledger.entries.first() {
        gaps::restore_gaps(relaid, entry)?;
    }
    let digest = seal_digest(relaid);
    fs::write(out_wire, relaid).map_err(|e| e.to_string())?;
    fs::write(seal_path, format!("{digest}\n")).map_err(|e| e.to_string())
}

pub fn seal_digest(buf: &[u8]) -> String {
    let hash = Sha256::digest(buf);
    hex::encode(hash)
}
