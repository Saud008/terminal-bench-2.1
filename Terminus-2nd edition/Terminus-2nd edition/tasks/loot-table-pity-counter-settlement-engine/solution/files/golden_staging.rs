use sha2::{Digest, Sha256};

use crate::envelope::canonical_body_json;
use crate::model::{PullEvent, StagingSnapshot};

pub fn sort_events(events: &[PullEvent]) -> Vec<PullEvent> {
    let mut out = events.to_vec();
    out.sort_by(|a, b| {
        (a.timestamp_ms, a.seq, a.event_id.as_str()).cmp(&(b.timestamp_ms, b.seq, b.event_id.as_str()))
    });
    out
}

pub fn compute_events_digest(events: &[PullEvent]) -> Result<String, String> {
    let ordered = sort_events(events);
    let mut parts = Vec::new();
    for event in ordered {
        let value = serde_json::to_value(&event).map_err(|e| e.to_string())?;
        parts.push(canonical_body_json(&value)?);
    }
    let payload = parts.join("\n");
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
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

pub fn verify_staging_digest(staging: &StagingSnapshot) -> Result<(), String> {
    let expected = compute_events_digest(&staging.events)?;
    if expected != staging.events_digest {
        return Err("staging events_digest mismatch".to_string());
    }
    Ok(())
}
