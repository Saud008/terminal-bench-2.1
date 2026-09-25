use crate::types::{ClosureRow, LatticeStation};

/// Rank stations for the residual-closure atlas.
pub fn rank_stations(stations: &[LatticeStation]) -> Vec<ClosureRow> {
    let mut rows: Vec<ClosureRow> = stations
        .iter()
        .map(|s| ClosureRow {
            station_id: s.station_id.clone(),
            residual_area_u64: s.residual_area_u64,
            vertex_count: s.vertex_count,
            rank: 0,
        })
        .collect();
    rows.sort_by(|a, b| a.station_id.cmp(&b.station_id));
    for (i, r) in rows.iter_mut().enumerate() {
        r.rank = i + 1;
    }
    rows
}
