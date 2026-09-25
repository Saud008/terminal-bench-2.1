//! Hot split cache — contract in /app/docs/merge-metadata.md.

use std::collections::HashMap;

#[derive(Default)]
pub struct HotCache {
    entries: HashMap<String, Vec<i64>>,
}

impl HotCache {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn load_split(&mut self, split_id: &str, doc_ids: Vec<i64>) {
        self.entries.insert(split_id.to_string(), doc_ids);
    }

    pub fn get(&self, split_id: &str) -> Option<&Vec<i64>> {
        self.entries.get(split_id)
    }

    pub fn invalidate(&mut self, split_id: &str) {
        self.entries.remove(split_id);
    }
}
