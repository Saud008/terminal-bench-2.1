use serde::{Deserialize, Serialize};

use crate::model::ParsedSentence;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PendingGroup {
    pub merge_key: String,
    pub talker: String,
    pub sentence: String,
    pub multipart_total: u32,
    pub fragments: Vec<ParsedSentence>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SessionState {
    pub version: u32,
    pub rmc_date: Option<String>,
    pub rmc_time: Option<String>,
    pub pending: Vec<PendingGroup>,
}

impl Default for SessionState {
    fn default() -> Self {
        Self {
            version: 1,
            rmc_date: None,
            rmc_time: None,
            pending: Vec::new(),
        }
    }
}
