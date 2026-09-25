use std::collections::HashSet;

pub fn first_duplicate_within(transcript_ids: &[String]) -> Option<String> {
    let mut seen = HashSet::new();
    for id in transcript_ids {
        if !seen.insert(id.clone()) {
            return Some(id.clone());
        }
    }
    None
}
