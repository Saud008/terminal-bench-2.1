use sha2::{Digest, Sha256};

use crate::model::{PullEvent, StagingSnapshot};

pub fn sort_events(events: &[PullEvent]) -> Vec<PullEvent> {
    let mut out = events.to_vec();
    out.sort_by(|a, b| a.event_id.cmp(&b.event_id));
    out
}

pub fn compute_events_digest(events: &[PullEvent]) -> Result<String, String> {
    let ordered = sort_events(events);
    let mut hasher = Sha256::new();
    for event in ordered {
        let raw = serde_json::to_string(&event).map_err(|e| e.to_string())?;
        hasher.update(raw.as_bytes());
    }
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn build_staging(
    events: Vec<PullEvent>,
    season_id: String,
    pool_epoch: u64,
    staging_generation: u64,
) -> Result<StagingSnapshot, String> {
    let events_digest = compute_events_digest(&events)?;
    Ok(StagingSnapshot {
        events,
        events_digest,
        season_id,
        pool_epoch,
        staging_generation,
    })
}

pub fn verify_staging_digest(_staging: &StagingSnapshot) -> Result<(), String> {
    Ok(())
}
