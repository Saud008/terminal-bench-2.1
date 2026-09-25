use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub docid: String,
    pub body: String,
    pub synonyms: BTreeMap<String, Vec<String>>,
    pub insertion_order: u64,
}
