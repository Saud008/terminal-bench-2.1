use crate::types::StagingFile;

pub fn snapshot_link_ok(staging: &StagingFile) -> bool {
    staging.snapshot_version == staging.targets_version
}
