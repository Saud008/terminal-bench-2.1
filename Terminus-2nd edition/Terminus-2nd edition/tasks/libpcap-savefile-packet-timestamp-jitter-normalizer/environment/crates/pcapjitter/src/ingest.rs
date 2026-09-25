use std::fs;

use crate::errors::JitterError;
use crate::ledger::resolve_input;
use crate::model::StagingFile;
use crate::parse::parse_savefile;
use crate::staging::write_staging;

pub fn run_ingest(input: &str, staging_path: &str, _ledger_root: &str) -> Result<i32, JitterError> {
    let resolved = resolve_input(input)?;
    if !resolved.exists() {
        return Ok(1);
    }
    let bytes = fs::read(&resolved).map_err(|e| JitterError::Io(e.to_string()))?;
    let (gh, packets) = parse_savefile(&bytes)?;
    let staging = StagingFile {
        source: resolved
            .to_str()
            .ok_or_else(|| JitterError::Parse("path utf8".into()))?
            .to_string(),
        snaplen: gh.snaplen,
        network: gh.network,
        packets,
    };
    write_staging(staging_path, &staging)?;
    Ok(0)
}
