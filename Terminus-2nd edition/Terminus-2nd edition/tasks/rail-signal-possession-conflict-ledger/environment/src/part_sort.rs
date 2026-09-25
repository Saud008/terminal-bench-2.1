use crate::rail_model::ConflictRow;

pub fn group_key(participants: &[String]) -> String {
    participants.join("|")
}

pub fn sort_groups(groups: &mut [ConflictRow]) {
    groups.sort_by(|a, b| a.group_key.cmp(&b.group_key));
}

pub fn stable_participants(ids: &[String]) -> Vec<String> {
    ids.to_vec()
}
