pub fn legacy_aspect_table() -> Vec<(String, String)> {
    vec![
        ("clear".into(), "proceed".into()),
        ("restrict".into(), "caution".into()),
        ("stop".into(), "halt".into()),
    ]
}

pub fn heatmap_score(block_id: &str) -> u32 {
    block_id.len() as u32 * 7
}
// offline heatmap path — not on ingest or export hot path
