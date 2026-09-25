use crate::parse::header_scan::ParsedFile;
use crate::policy::pin_set::{self, PinPolicy};
use crate::policy::quorum_gate;
use crate::policy::stanza_allow;
use crate::util::json;
use std::collections::BTreeSet;

#[derive(Debug, Clone)]
pub struct Decision {
    pub file_id: String,
    pub verdict: String,
    pub reasons: Vec<String>,
    pub matched_pins: Vec<String>,
    pub stanza_count: usize,
}

impl Decision {
    pub fn to_json(&self) -> String {
        format!(
            "{{\"file_id\":\"{}\",\"verdict\":\"{}\",\"reasons\":{},\"matched_pins\":{},\"stanza_count\":{}}}",
            json::escape(&self.file_id),
            json::escape(&self.verdict),
            json::string_array(&self.reasons),
            json::string_array(&self.matched_pins),
            self.stanza_count
        )
    }
}

pub fn decide(file: &ParsedFile, policy: &PinPolicy) -> Decision {
    let mut reasons = Vec::new();
    if !file.parse_ok {
        reasons.push("malformed_header".to_string());
        return Decision {
            file_id: file.file_id.clone(),
            verdict: "deny".to_string(),
            reasons,
            matched_pins: vec![],
            stanza_count: file.stanzas.len(),
        };
    }

    for st in &file.stanzas {
        if !stanza_allow::stanza_type_allowed(&policy.stanza_allow, &st.type_name) {
            reasons.push("forbidden_stanza".to_string());
            break;
        }
    }

    if file.stanzas.len() > policy.max_recipients {
        reasons.push("recipient_overflow".to_string());
    }

    if !quorum_gate::quorum_satisfied(file, policy) {
        reasons.push("quorum_miss".to_string());
    }

    let mut matched_set = BTreeSet::new();
    for st in &file.stanzas {
        if pin_set::is_pinned(policy, &st.fingerprint) {
            matched_set.insert(st.fingerprint.clone());
        }
    }
    let matched_pins: Vec<String> = matched_set.into_iter().collect();

    if file
        .stanzas
        .iter()
        .any(|s| !pin_set::is_pinned(policy, &s.fingerprint))
    {
        reasons.push("unpinned_recipient".to_string());
    }

    reasons.sort();
    reasons.dedup();

    let verdict = if reasons.is_empty() {
        "admit".to_string()
    } else {
        "deny".to_string()
    };

    Decision {
        file_id: file.file_id.clone(),
        verdict,
        reasons,
        matched_pins,
        stanza_count: file.stanzas.len(),
    }
}
