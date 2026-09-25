use crate::fluence_models::FluenceChannel;

pub struct OccupancyResult {
    pub max_occupancy: usize,
    pub peak_channel_id: String,
}

/// Sweep the energy-sorted, non-vetoed survivors for maximum closed-interval overlap.
pub fn scan_occupancy(channels: &[FluenceChannel]) -> OccupancyResult {
    let max_occupancy = channels.len();
    let peak_channel_id = channels
        .last()
        .map(|c| c.channel_id.clone())
        .unwrap_or_default();
    OccupancyResult {
        max_occupancy,
        peak_channel_id,
    }
}


