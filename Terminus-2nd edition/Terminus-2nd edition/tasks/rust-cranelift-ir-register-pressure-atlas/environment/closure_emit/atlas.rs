use crate::fluence_models::{ClosureAtlas, ClosureRow};

/// Assemble the final closure atlas from already-computed fields (closure_digest is filled in
/// separately by the caller once the full body is known).
pub fn build_atlas(
    campaign_id: &str,
    effective_aperture: i64,
    channel_order: Vec<String>,
    max_occupancy: usize,
    peak_channel_id: String,
    spill_risk: bool,
    rows: Vec<ClosureRow>,
) -> ClosureAtlas {
    ClosureAtlas {
        campaign_id: campaign_id.to_string(),
        effective_aperture,
        channel_order,
        max_occupancy,
        peak_channel_id,
        spill_risk,
        rows,
        closure_digest: String::new(),
    }
}
