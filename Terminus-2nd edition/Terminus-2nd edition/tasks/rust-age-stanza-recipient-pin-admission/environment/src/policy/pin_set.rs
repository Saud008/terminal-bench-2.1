use crate::util::json;
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct PinPolicy {
    pub pins: BTreeSet<String>,
    pub stanza_allow: Vec<String>,
    pub quorum_k: usize,
    pub max_recipients: usize,
}

pub fn load_policy(path: &Path) -> Result<PinPolicy, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let pins: BTreeSet<String> = json::extract_string_array(&raw, "pins")?
        .into_iter()
        .collect();
    let stanza_allow = json::extract_string_array(&raw, "stanza_allow")?;
    let quorum_k = json::extract_usize(&raw, "quorum_k")?;
    let max_recipients = json::extract_usize(&raw, "max_recipients")?;
    Ok(PinPolicy {
        pins,
        stanza_allow,
        quorum_k,
        max_recipients,
    })
}

pub fn is_pinned(policy: &PinPolicy, fp: &str) -> bool {
    policy.pins.contains(fp)
}
