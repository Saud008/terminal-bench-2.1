use anyhow::Result;

use crate::mp93::{export_digest, verify_ledger_envelope};
use crate::kx42_snapshot::{read_envelope, StagingEnvelope};

pub fn verify_export_binding(envelope: &StagingEnvelope) -> Result<()> {
    verify_ledger_envelope(
        &envelope.wire_digest,
        &export_digest(&envelope.scene),
        envelope.scene.revision,
    )
}

pub fn run_verify() -> Result<bool> {
    let envelope = read_envelope()?;
    match verify_export_binding(&envelope) {
        Ok(()) => Ok(true),
        Err(_) => Ok(false),
    }
}
