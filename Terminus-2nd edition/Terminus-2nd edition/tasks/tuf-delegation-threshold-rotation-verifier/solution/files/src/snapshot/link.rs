use crate::types::StagingFile;

pub fn snapshot_link_ok(staging: &StagingFile) -> bool {
    staging.snapshot_targets_version == staging.targets_version
}
