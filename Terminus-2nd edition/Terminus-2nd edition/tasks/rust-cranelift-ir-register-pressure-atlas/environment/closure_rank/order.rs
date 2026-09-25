use crate::fluence_models::{ClosureRow, FluenceChannel};

/// Rank non-vetoed channels for the residual-occupancy closure atlas.
pub fn rank_channels(channels: &[FluenceChannel]) -> Vec<ClosureRow> {
    let mut rows: Vec<ClosureRow> = channels
        .iter()
        .filter(|c| !c.vetoed)
        .map(|c| ClosureRow {
            channel_id: c.channel_id.clone(),
            residual_counts: c.residual_counts,
            rank: 0,
            vetoed: false,
        })
        .collect();
    rows.sort_by(|a, b| a.channel_id.cmp(&b.channel_id));
    for (i, r) in rows.iter_mut().enumerate() {
        r.rank = i + 1;
    }
    rows
}


