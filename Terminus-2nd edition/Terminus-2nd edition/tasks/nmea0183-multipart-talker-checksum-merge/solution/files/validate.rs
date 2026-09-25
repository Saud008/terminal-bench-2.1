use crate::model::MergeSnapshot;

pub fn validate_snapshot(snapshot: &MergeSnapshot) -> Result<(), String> {
    for group in &snapshot.groups {
        if !group.merge_key.starts_with(&format!("{}:", group.talker)) {
            return Err(format!(
                "merge_key {} must begin with canonical talker {}",
                group.merge_key, group.talker
            ));
        }
    }
    Ok(())
}
