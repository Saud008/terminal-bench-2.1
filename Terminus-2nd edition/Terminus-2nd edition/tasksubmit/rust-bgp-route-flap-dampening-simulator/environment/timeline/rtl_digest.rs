use sha2::{Digest, Sha256};

pub fn slot_digest(
    peer_id: &str,
    prefix: &str,
    penalty_now: u64,
    reuse_threshold: u64,
    _ms_to_reuse: u64,
    _forecast_anchor_ms: u64,
) -> String {
    let preimage = format!("{peer_id}|{prefix}|{penalty_now}|{reuse_threshold}");
    let digest = Sha256::digest(preimage.as_bytes());
    hex::encode(digest)
}
