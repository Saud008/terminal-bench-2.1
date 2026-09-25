use sha2::{Digest, Sha256};

pub fn max_skew(rows: &[(u32, u32)]) -> u32 {
    rows.iter().map(|(a, b)| a.abs_diff(*b)).max().unwrap_or(0)
}

pub fn risk_digest(trial_id: &str, protocol_digest: &str, max_skew: u32, run_id: u32) -> String {
    let preimage = format!("{trial_id}|{protocol_digest}|{max_skew}|{run_id}");
    hex::encode(Sha256::digest(preimage.as_bytes()))
}
