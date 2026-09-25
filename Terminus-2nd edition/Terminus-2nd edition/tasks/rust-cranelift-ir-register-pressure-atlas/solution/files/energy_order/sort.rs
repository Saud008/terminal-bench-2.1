use crate::fluence_models::FluenceChannel;

/// Sort survivors by quantized energy ascending, tie-break channel_id ascending.
pub fn sort_channels(channels: &mut Vec<FluenceChannel>) {
    channels.sort_by(|a, b| {
        a.energy_q
            .partial_cmp(&b.energy_q)
            .unwrap()
            .then_with(|| a.channel_id.cmp(&b.channel_id))
    });
}
