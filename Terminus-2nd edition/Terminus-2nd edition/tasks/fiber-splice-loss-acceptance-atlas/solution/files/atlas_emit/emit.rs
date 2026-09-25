use crate::types::{AcceptanceAtlas, BindStage};
use sha2::{Digest, Sha256};
use std::fs;

pub fn publish_verdict(run_id: &str, bind_path: &str, output_path: &str) -> Result<(), String> {
    let raw = fs::read_to_string(bind_path).map_err(|e| e.to_string())?;
    let bind: BindStage = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let accepted = bind.segments.iter().filter(|s| s.accepted).count() as u32;
    let rejected = bind.segments.len() as u32 - accepted;
    let event_count: u32 = bind.segments.iter().map(|s| s.bound_event_count).sum();
    let mut atlas = AcceptanceAtlas {
        run_id: run_id.to_string(),
        event_count,
        accepted_segment_count: accepted,
        rejected_segment_count: rejected,
        suppressed_duplicate_count: bind.suppressed_duplicate_count,
        segments: bind.segments,
        audit_digest: String::new(),
    };
    atlas.audit_digest = audit_digest(&atlas);
    fs::write(output_path, serde_json::to_string_pretty(&atlas).unwrap()).map_err(|e| e.to_string())
}

fn audit_digest(atlas: &AcceptanceAtlas) -> String {
    let mut ids: Vec<String> = atlas.segments.iter().map(|s| s.segment_id.clone()).collect();
    ids.sort();
    let body = serde_json::json!({
        "run_id": atlas.run_id,
        "event_count": atlas.event_count,
        "accepted_segment_count": atlas.accepted_segment_count,
        "segment_ids": ids,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}
