use std::path::Path;

use crate::model::{GapRange, LedgerExport, ReplayExport, SimExport, SimState};
use crate::sim::hash_state;
use crate::staging::{read_staging, StagingSnapshot};

pub fn publish_export(export_path: &Path) -> Result<ReplayExport, String> {
    let snap = read_staging()?;
    build_export(&snap, export_path)
}

fn build_export(snap: &StagingSnapshot, export_path: &Path) -> Result<ReplayExport, String> {
    let sim = SimState {
        tick: snap.sim.tick,
        accumulator: snap.sim.accumulator,
        mix: snap.sim.mix,
        inputs_applied: snap.sim.inputs_applied,
    };
    let export = ReplayExport {
        bundle_id: snap.bundle_id.clone(),
        seed: snap.seed,
        client_id: snap.client_id,
        state_hash: hash_state(&sim, snap.client_id, snap.seed),
        ledger: LedgerExport {
            playhead: snap.ledger_raw.playhead,
            gaps: merge_ranges(&snap.ledger_raw.gaps_raw),
            duplicate_acks: snap.ledger_raw.duplicate_acks,
            peer_loss_gaps: merge_ranges(&snap.ledger_raw.peer_loss_raw),
            frames_received: snap.ledger_raw.frames_received,
        },
        sim: SimExport {
            tick: sim.tick,
            accumulator: sim.accumulator,
            mix: sim.mix,
            inputs_applied: sim.inputs_applied,
        },
    };
    let text = serde_json::to_string_pretty(&export).map_err(|e| e.to_string())?;
    if let Some(parent) = export_path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    std::fs::write(export_path, text).map_err(|e| e.to_string())?;
    Ok(export)
}

pub fn merge_ranges(raw: &[(u32, u32)]) -> Vec<GapRange> {
    if raw.is_empty() {
        return Vec::new();
    }
    let mut pairs = raw.to_vec();
    pairs.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));
    let mut out = Vec::new();
    let (mut start, mut end) = pairs[0];
    for (s, e) in pairs.into_iter().skip(1) {
        if s <= end.wrapping_add(1) {
            if e > end {
                end = e;
            }
        } else {
            out.push(GapRange { start, end });
            start = s;
            end = e;
        }
    }
    out.push(GapRange { start, end });
    out
}
