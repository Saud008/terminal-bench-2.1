use crate::error::{Result, XanesError};

pub fn edge_ordinal(edge_code: &str) -> Result<u32> {
    match edge_code {
        "K" => Ok(1),
        "L1" => Ok(2),
        "L2" => Ok(3),
        "L3" => Ok(4),
        "M1" => Ok(5),
        "M2" => Ok(6),
        "M3" => Ok(7),
        "M4" => Ok(8),
        "M5" => Ok(9),
        other => Err(XanesError::UnknownEdge(other.to_string())),
    }
}

#[derive(Clone, Debug)]
pub struct ChannelRef {
    pub channel_id: String,
    pub atomic_number: u32,
    pub edge_code: String,
}

pub fn sort_channels(mut channels: Vec<ChannelRef>) -> Result<Vec<String>> {
    channels.sort_by(|a, b| a.channel_id.cmp(&b.channel_id));
    Ok(channels.into_iter().map(|c| c.channel_id).collect())
}
