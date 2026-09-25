use std::collections::HashMap;

use crate::merge::multipart;
use crate::model::{MergeGroup, ParsedSentence};
use crate::session::store::PendingGroup;

pub struct PendingStore {
    groups: HashMap<String, Vec<ParsedSentence>>,
}

impl PendingStore {
    pub fn new() -> Self {
        Self { groups: HashMap::new() }
    }

    pub fn from_groups(groups: Vec<PendingGroup>) -> Self {
        let mut map = HashMap::new();
        for group in groups {
            map.insert(group.merge_key, group.fragments);
        }
        Self { groups: map }
    }

    pub fn into_groups(self) -> Vec<PendingGroup> {
        self.groups
            .into_iter()
            .filter(|(_, fragments)| {
                fragments.iter().any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false))
            })
            .map(|(merge_key, fragments)| {
                let first = fragments.first().cloned().unwrap_or(ParsedSentence {
                    raw: String::new(),
                    talker: String::new(),
                    sentence: String::new(),
                    fields: Vec::new(),
                    is_multipart: true,
                });
                let talker = crate::talker::normalize::canonical_talker(&first.talker);
                let sentence = first.sentence.clone();
                let multipart_total = first
                    .fields
                    .first()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or(1);
                PendingGroup {
                    merge_key,
                    talker,
                    sentence,
                    multipart_total,
                    fragments,
                }
            })
            .collect()
    }

    pub fn clear_all(&mut self) {
        self.groups.clear();
    }

    pub fn is_empty(&self) -> bool {
        self.groups.is_empty()
    }

    pub fn take_fragments(&mut self, merge_key: &str) -> Vec<ParsedSentence> {
        self.groups.remove(merge_key).unwrap_or_default()
    }

    pub fn stash_incomplete(&mut self, merge_key: String, fragments: Vec<ParsedSentence>) {
        self.groups.insert(merge_key, fragments);
    }

    pub fn group_from_bucket(
        &self,
        merge_key: &str,
        fragments: &[ParsedSentence],
        emit_incomplete: bool,
    ) -> Option<MergeGroup> {
        if fragments.is_empty() {
            return None;
        }
        let first = &fragments[0];
        let talker = crate::talker::normalize::canonical_talker(&first.talker);
        let (multipart_total, fragments_merged, payload_fields) =
            multipart::merge_payload(fragments);
        if !emit_incomplete && fragments_merged < multipart_total {
            return None;
        }
        Some(MergeGroup {
            merge_key: merge_key.to_string(),
            talker,
            sentence: first.sentence.clone(),
            multipart_total,
            fragments_merged,
            payload_fields,
            utc_iso: None,
        })
    }

    pub fn finalize_bucket(
        &mut self,
        merge_key: String,
        fragments: Vec<ParsedSentence>,
        use_session: bool,
        out: &mut Vec<MergeGroup>,
    ) {
        if fragments.is_empty() {
            return;
        }
        let has_one = fragments
            .iter()
            .any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false));
        if !has_one {
            // orphan drop
            return;
        }
        let total = fragments[0]
            .fields
            .first()
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(1);
        let merged = {
            let mut nums = std::collections::HashSet::new();
            for f in &fragments {
                if let Some(n) = f.fields.get(1) {
                    nums.insert(n.clone());
                }
            }
            nums.len() as u32
        };
        if use_session && merged < total {
            self.stash_incomplete(merge_key, fragments);
            return;
        }
        if let Some(group) = self.group_from_bucket(&merge_key, &fragments, true) {
            out.push(group);
        }
    }

    pub fn merge_with_pending(&mut self, merge_key: &str, incoming: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
        let mut pending = self.take_fragments(merge_key);
        pending.extend(incoming);
        pending.sort_by_key(|sentence| {
            sentence
                .fields
                .get(1)
                .and_then(|v| v.parse::<u32>().ok())
                .unwrap_or(0)
        });
        crate::session::reconcile::reconcile_fragments(pending)
    }
}

impl Default for PendingStore {
    fn default() -> Self {
        Self::new()
    }
}
