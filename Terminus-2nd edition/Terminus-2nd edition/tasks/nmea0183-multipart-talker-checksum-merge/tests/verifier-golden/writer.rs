use sha2::{Digest, Sha256};
use serde::Serialize;

use crate::model::{MergeGroup, MergeSnapshot, RejectedLine};

#[derive(Serialize)]
struct DigestPayload<'a> {
    groups: &'a [MergeGroup],
    rejected: &'a [RejectedLine],
}

pub fn finalize_digest(snapshot: &mut MergeSnapshot) {
    let mut groups = snapshot.groups.clone();
    let mut rejected = snapshot.rejected.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    rejected.sort_by(|a, b| a.line.cmp(&b.line));
    let digest = digest_parts(&groups, &rejected);
    snapshot.snapshot_digest = digest;
}

pub fn verify_digest(snapshot: &MergeSnapshot) -> Result<(), String> {
    let mut groups = snapshot.groups.clone();
    let mut rejected = snapshot.rejected.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    rejected.sort_by(|a, b| a.line.cmp(&b.line));
    let expected = digest_parts(&groups, &rejected);
    if expected != snapshot.snapshot_digest {
        return Err("digest mismatch".into());
    }
    Ok(())
}

fn digest_parts(groups: &[MergeGroup], rejected: &[RejectedLine]) -> String {
    // Serialize via typed structs so field order matches declaration order
    // (serde_json::json! alphabetizes keys and breaks digest interoperability).
    let bytes = serde_json::to_vec(&DigestPayload { groups, rejected }).unwrap_or_default();
    hex::encode(Sha256::digest(&bytes))
}
