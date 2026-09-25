use crate::model::{MergeReport, MergeSnapshot};

/// BROKEN: reorders groups by merge_key.
pub fn build_report(snapshot: &MergeSnapshot) -> MergeReport {
    let mut groups = snapshot.groups.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    MergeReport {
        groups,
        rejected: snapshot.rejected.clone(),
        snapshot_digest: snapshot.snapshot_digest.clone(),
    }
}
