use std::fs;
use std::path::Path;

use crate::ledger::{apply_peer_ack, record_frame, recompute_playhead};
use crate::model::{BundleSpec, LedgerState, SimState};
use crate::replay::mutate_seq;
use crate::sim::apply_frame_inputs;
use crate::staging::write_staging;
use crate::wire::parse_frame;

pub fn run_ingest(bundle_path: &Path, seed: u64) -> Result<(), String> {
    let text = fs::read_to_string(bundle_path).map_err(|e| e.to_string())?;
    let bundle: BundleSpec = serde_json::from_str(&text).map_err(|e| e.to_string())?;
    let mut ledger = LedgerState::default();
    let mut sim = SimState::default();
    let mut client_id = 0u32;

    for pkt in &bundle.packets {
        let raw = hex::decode(pkt.hex.trim()).map_err(|e| e.to_string())?;
        let raw = mutate_seq(&raw, seed);
        let frame = parse_frame(&raw).map_err(|e| e.to_string())?;
        client_id = frame.client_id;
        record_frame(&mut ledger, frame.frame_seq);
        recompute_playhead(&mut ledger);
        apply_peer_ack(&mut ledger, frame.ack_base, frame.loss_mask);
        apply_frame_inputs(&mut sim, &frame);
    }

    write_staging(&bundle.bundle_id, seed, client_id, &ledger, &sim)
}
