use crate::types::{ClosureAtlas, ClosureRow, ClosureSummary};

fn is_wrap_part(station_id: &str) -> bool {
    station_id.ends_with("-W") || station_id.ends_with("-E")
}

pub fn build_atlas(campaign_id: &str, rows: &[ClosureRow], digest: &str) -> ClosureAtlas {
    let areas: Vec<u64> = rows.iter().map(|r| r.residual_area_u64).collect();
    let wrap_parts = rows.iter().filter(|r| is_wrap_part(&r.station_id)).count();
    let summary = ClosureSummary {
        total_stations: rows.len(),
        wrap_parts,
        max_area: areas.iter().copied().max().unwrap_or(0),
        min_area: areas.iter().copied().min().unwrap_or(0),
    };
    ClosureAtlas {
        campaign_id: campaign_id.to_string(),
        rows: rows.to_vec(),
        summary,
        closure_digest: digest.to_string(),
    }
}
