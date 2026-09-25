use crate::half_life_bias;
use crate::route_model::{fallback_peer, PeerDampening};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn load_table(root: &str, peers: &[String]) -> Result<BTreeMap<String, PeerDampening>, String> {
    let bias = half_life_bias();
    let mut out = BTreeMap::new();
    for peer in peers {
        let path = Path::new(root).join("policies").join(format!("{peer}.json"));
        let mut row: PeerDampening = if path.is_file() {
            serde_json::from_str(&fs::read_to_string(&path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?
        } else {
            fallback_peer(peer)
        };
        if bias != 0 {
            row.half_life_ms = row.half_life_ms.saturating_add_signed(bias);
        }
        if row.reuse_threshold * 2 >= row.suppress_threshold {
            return Err(format!("invalid reuse for peer {peer}"));
        }
        out.insert(peer.clone(), row);
    }
    Ok(out)
}

pub fn row_for(table: &BTreeMap<String, PeerDampening>, peer: &str) -> PeerDampening {
    table
        .get(peer)
        .cloned()
        .unwrap_or_else(|| fallback_peer(peer))
}
