use crate::route_model::{FeedEvent, FeedKind};

pub fn parse_lines(raw: &[u8]) -> Result<Vec<FeedEvent>, String> {
    let text = std::str::from_utf8(raw).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in text.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn kind_tag(kind: &FeedKind) -> u8 {
    match kind {
        FeedKind::Announce => 0,
        FeedKind::Withdraw => 1,
    }
}
