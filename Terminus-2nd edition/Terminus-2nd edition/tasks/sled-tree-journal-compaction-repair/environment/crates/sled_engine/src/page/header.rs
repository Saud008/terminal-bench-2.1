use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct PageHeader {
    pub page_id: String,
    pub generation: u64,
    pub high_key: Option<String>,
}

impl PageHeader {
    pub fn new(page_id: impl Into<String>, generation: u64, high_key: Option<String>) -> Self {
        Self {
            page_id: page_id.into(),
            generation,
            high_key,
        }
    }
}
