use crate::model::{MergeReport, MergeSnapshot};

pub fn build_report(snapshot: &MergeSnapshot) -> MergeReport {
    MergeReport {
        groups: snapshot.groups.clone(),
        rejected: snapshot.rejected.clone(),
        snapshot_digest: snapshot.snapshot_digest.clone(),
    }
}
