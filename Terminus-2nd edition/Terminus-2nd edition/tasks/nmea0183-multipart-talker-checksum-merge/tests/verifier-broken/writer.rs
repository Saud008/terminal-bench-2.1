use sha2::{Digest, Sha256};

use crate::model::MergeSnapshot;

/// BROKEN: digests unsorted groups as-is.
pub fn finalize_digest(snapshot: &mut MergeSnapshot) {
    let payload = serde_json::json!({
        "groups": snapshot.groups,
        "rejected": snapshot.rejected,
    });
    let bytes = serde_json::to_vec(&payload).unwrap_or_default();
    let digest = Sha256::digest(&bytes);
    snapshot.snapshot_digest = hex::encode(digest);
}

pub fn verify_digest(snapshot: &MergeSnapshot) -> Result<(), String> {
    let mut tmp = snapshot.clone();
    let claimed = tmp.snapshot_digest.clone();
    finalize_digest(&mut tmp);
    if tmp.snapshot_digest != claimed {
        return Err("digest mismatch".into());
    }
    Ok(())
}
