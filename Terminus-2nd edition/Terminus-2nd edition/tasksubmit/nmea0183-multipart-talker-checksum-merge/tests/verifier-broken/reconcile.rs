use std::collections::HashMap;

use crate::model::ParsedSentence;

/// When pending fragments merge with new input, duplicate message numbers keep the
/// earliest stored fragment (session replay contract in `/app/docs/merge-contract.md`).
pub fn reconcile_fragments(fragments: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
    let mut by_num: HashMap<String, ParsedSentence> = HashMap::new();
    for sentence in fragments {
        let num = sentence
            .fields
            .get(1)
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        by_num.entry(num).or_insert(sentence);
    }
    let mut out: Vec<ParsedSentence> = by_num.into_values().collect();
    out.sort_by_key(|sentence| {
        sentence
            .fields
            .get(1)
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(0)
    });
    out
}
