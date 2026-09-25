use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Document {
    pub docid: String,
    pub title: String,
    pub body: String,
    pub brand: String,
    pub insertion_order: u64,
}

impl Document {
    pub fn searchable_text(&self) -> String {
        format!("{} {}", self.title, self.body)
    }
}
