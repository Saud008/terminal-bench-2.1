use crate::types::ClosureRow;
use sha2::{Digest, Sha256};

/// Build closure_digest over ranked rows.
pub fn closure_digest(rows: &[ClosureRow]) -> String {
    let lines: Vec<String> = rows
        .iter()
        .map(|r| format!("{}|{}|{}", r.station_id, r.residual_area_u64, r.vertex_count))
        .collect();
    let body = lines.join("
");
    let hash = Sha256::digest(body.as_bytes());
    hex::encode(hash)
}
