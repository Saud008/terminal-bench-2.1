use std::collections::HashSet;

pub fn duplicate_ids(ids: &[String]) -> HashSet<String> {
    let mut seen = HashSet::new();
    let mut dups = HashSet::new();
    for id in ids {
        if !seen.insert(id.clone()) {
            dups.insert(id.clone());
        }
    }
    dups
}

pub fn first_duplicate_within(transcript_ids: &[String]) -> Option<String> {
    duplicate_ids(transcript_ids).into_iter().next()
}
