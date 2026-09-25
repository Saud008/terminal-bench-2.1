use crate::fluence_models::ClosureAtlas;
use sha2::{Digest, Sha256};

/// Canonical closure digest over every atlas field except closure_digest, keys sorted at every
/// nesting level.
pub fn closure_digest(atlas: &ClosureAtlas) -> String {
    let order_json = serde_json::to_string(&atlas.channel_order).unwrap_or_default();
    let rows_json = serde_json::to_string(&atlas.rows).unwrap_or_default();
    let body = format!(
        "{{\"campaign_id\":\"{}\",\"effective_aperture\":{},\"channel_order\":{},\"max_occupancy\":{},\"peak_channel_id\":\"{}\",\"spill_risk\":{},\"rows\":{}}}",
        atlas.campaign_id,
        atlas.effective_aperture,
        order_json,
        atlas.max_occupancy,
        atlas.peak_channel_id,
        atlas.spill_risk,
        rows_json,
    );
    let hash = Sha256::digest(body.as_bytes());
    hex::encode(hash)
}

/// Render the sealed atlas body for the output file.
pub fn render_atlas_body(atlas: &ClosureAtlas) -> String {
    serde_json::to_string_pretty(atlas).expect("pretty atlas")
}


