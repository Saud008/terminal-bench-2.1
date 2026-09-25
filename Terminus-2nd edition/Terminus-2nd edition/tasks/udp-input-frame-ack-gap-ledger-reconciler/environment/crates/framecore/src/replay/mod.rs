use std::path::Path;

use crate::export::publish_export;
use crate::ingest::run_ingest;
use crate::model::ReplayExport;

pub fn seed_client_id(base: u32, seed: u64) -> u32 {
    base ^ (seed as u32).wrapping_mul(0x9E37_79B9)
}

pub fn mutate_seq(raw: &[u8], seed: u64) -> Vec<u8> {
    let mut out = raw.to_vec();
    if out.len() >= 12 {
        let seq = u32::from_le_bytes(out[8..12].try_into().unwrap());
        let bump = (seed.wrapping_mul(17)) as u32;
        out[8..12].copy_from_slice(&seq.wrapping_add(bump).to_le_bytes());
    }
    if out.len() >= 8 {
        let cid = u32::from_le_bytes(out[4..8].try_into().unwrap());
        let sid = seed_client_id(cid, seed);
        out[4..8].copy_from_slice(&sid.to_le_bytes());
    }
    out
}

pub fn run_replay(bundle_path: &Path, seed: u64, export_path: &Path) -> Result<ReplayExport, String> {
    run_ingest(bundle_path, seed)?;
    publish_export(export_path)
}
