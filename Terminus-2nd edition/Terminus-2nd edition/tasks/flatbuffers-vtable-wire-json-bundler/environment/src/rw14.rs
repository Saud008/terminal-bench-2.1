use anyhow::Result;



use crate::bd13::decode_buffer;

use crate::export;

use crate::guard;

use crate::je67;

use crate::zq81;

use crate::mp93::{append_ledger, verify_ledger_head};

use crate::kx42_snapshot::{load_snapshot, read_envelope, write_snapshot};



/// Ingest-phase entry: decode flatbuffer wire bytes, persist snapshot, append ledger.
pub fn stage_buffer(buf: &[u8]) -> Result<u32> {

    let scene = decode_buffer(buf)?;

    let revision = scene.revision;

    write_snapshot(&scene, buf)?;

    append_ledger(&scene, buf)?;

    Ok(revision)

}



pub fn export_staged(buf: &[u8], revision: u32) -> Result<String> {

    verify_ledger_head(buf, revision)?;

    let scene = load_snapshot(buf, revision)?;

    export::render_stdout(&scene)

}



pub fn export_from_state() -> Result<String> {

    let envelope = read_envelope()?;

    guard::verify_export_binding(&envelope)?;

    export::render_stdout(&envelope.scene)

}



pub fn decode_buffer_json(buf: &[u8]) -> Result<String> {

    let revision = stage_buffer(buf)?;

    export_staged(buf, revision)

}



pub fn verify_state() -> Result<bool> {

    guard::run_verify()

}

