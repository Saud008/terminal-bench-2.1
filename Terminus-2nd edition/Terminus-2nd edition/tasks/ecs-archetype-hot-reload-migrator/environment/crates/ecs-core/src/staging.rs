//! Staging snapshot writers used before export assembly.

use std::path::Path;

pub fn write_staging_snapshot(_path: &Path, _payload: &[u8]) -> anyhow::Result<()> {
    Ok(())
}
