use crate::fluence_models::FluenceChannel;

pub struct OccupancyResult {
    pub max_occupancy: usize,
    pub peak_channel_id: String,
}

/// Sweep the energy-sorted, non-vetoed survivors for maximum closed-interval overlap. The
/// maximum overlap of a set of closed intervals always occurs at one interval's start, so
/// evaluating each survivor's own start point is sufficient.
pub fn scan_occupancy(channels: &[FluenceChannel]) -> OccupancyResult {
    let survivors: Vec<&FluenceChannel> = channels.iter().filter(|c| !c.vetoed).collect();
    if survivors.is_empty() {
        return OccupancyResult {
            max_occupancy: 0,
            peak_channel_id: String::new(),
        };
    }
    let mut best_index = 0usize;
    let mut best_count = 0usize;
    for (i, ch) in survivors.iter().enumerate() {
        let start = ch.energy_q;
        let count = survivors
            .iter()
            .filter(|other| other.energy_q <= start && start <= other.energy_q + other.width_q)
            .count();
        if count > best_count {
            best_count = count;
            best_index = i;
        }
    }
    OccupancyResult {
        max_occupancy: best_count,
        peak_channel_id: survivors[best_index].channel_id.clone(),
    }
}
