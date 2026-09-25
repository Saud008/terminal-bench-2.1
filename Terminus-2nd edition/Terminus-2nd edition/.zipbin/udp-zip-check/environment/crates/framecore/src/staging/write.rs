use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::model::{LedgerState, SimState};

pub const STAGING_PATH: &str = "/app/state/replay-staging.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StagingLedgerRaw {
    pub playhead: u32,
    pub gaps_raw: Vec<(u32, u32)>,
    pub peer_loss_raw: Vec<(u32, u32)>,
    pub duplicate_acks: u32,
    pub frames_received: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StagingSim {
    pub tick: u64,
    pub accumulator: i64,
    pub mix: u64,
    pub inputs_applied: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StagingSnapshot {
    pub bundle_id: String,
    pub seed: u64,
    pub client_id: u32,
    pub ledger_raw: StagingLedgerRaw,
    pub sim: StagingSim,
}

fn normalize_tuple(start: u32, end: u32) -> (u32, u32) {
    if start <= end {
        (start, end)
    } else {
        (end, start)
    }
}

pub fn write_staging(
    bundle_id: &str,
    seed: u64,
    client_id: u32,
    ledger: &LedgerState,
    sim: &SimState,
) -> Result<(), String> {
    let peer_loss_raw: Vec<(u32, u32)> = ledger
        .peer_loss_gaps
        .iter()
        .map(|(s, e)| normalize_tuple(*s, *e))
        .collect();
    let snapshot = StagingSnapshot {
        bundle_id: bundle_id.to_string(),
        seed,
        client_id,
        ledger_raw: StagingLedgerRaw {
            playhead: ledger.playhead,
            gaps_raw: ledger.gaps.clone(),
            peer_loss_raw,
            duplicate_acks: ledger.duplicate_acks,
            frames_received: ledger.frames_received,
        },
        sim: StagingSim {
            tick: sim.tick,
            accumulator: sim.accumulator,
            mix: sim.mix,
            inputs_applied: sim.inputs_applied,
        },
    };
    let path = Path::new(STAGING_PATH);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(&snapshot).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| e.to_string())
}

pub fn read_staging() -> Result<StagingSnapshot, String> {
    let text = fs::read_to_string(STAGING_PATH).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}
