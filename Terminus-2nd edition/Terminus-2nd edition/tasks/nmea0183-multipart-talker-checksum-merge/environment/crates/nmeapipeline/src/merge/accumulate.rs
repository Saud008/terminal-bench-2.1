use crate::model::{MergeGroup, ParsedSentence};

/// Legacy decoy path — not on the hot path. Wrong merge order.
pub fn accumulate_groups(sentences: &[ParsedSentence]) -> Vec<MergeGroup> {
    sentences
        .iter()
        .map(|s| MergeGroup {
            merge_key: format!("{}:{}:1", s.talker, s.sentence),
            talker: s.talker.clone(),
            sentence: s.sentence.clone(),
            multipart_total: 1,
            fragments_merged: 1,
            payload_fields: s.fields.clone(),
            utc_iso: None,
        })
        .collect()
}
