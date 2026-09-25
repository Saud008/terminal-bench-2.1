use super::staging::MergeSnapshot;

pub fn validate_snapshot(snapshot: &MergeSnapshot) -> Result<(), String> {
    for group in &snapshot.groups {
        // Single-pass merges may emit incomplete multipart groups
        // (fragments_merged < multipart_total). Completeness is enforced by
        // session pending buffering when --state is used, not by this gate.
        // Export only requires canonical talker prefixes on merge_key.
        if !group.merge_key.starts_with(&format!("{}:", group.talker)) {
            return Err(format!(
                "merge_key {} must begin with canonical talker {}",
                group.merge_key, group.talker
            ));
        }
    }
    Ok(())
}
