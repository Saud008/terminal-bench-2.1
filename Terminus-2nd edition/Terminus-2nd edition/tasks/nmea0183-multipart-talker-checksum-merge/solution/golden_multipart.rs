use crate::model::ParsedSentence;

pub fn merge_payload(fragments: &[ParsedSentence]) -> (u32, u32, Vec<String>) {
    let mut sorted = fragments.to_vec();
    sorted.sort_by_key(|s| s.fields.get(1).and_then(|v| v.parse::<u32>().ok()).unwrap_or(0));
    let total = sorted
        .first()
        .and_then(|s| s.fields.first())
        .and_then(|v| v.parse().ok())
        .unwrap_or(1);
    let mut payload = Vec::new();
    for s in &sorted {
        if s.fields.len() > 3 {
            payload.extend(s.fields[3..].iter().cloned());
        }
    }
    (total, sorted.len() as u32, payload)
}

pub fn merge_key(talker: &str, sentence: &str, total: u32) -> String {
    format!("{talker}:{sentence}:{total}")
}
