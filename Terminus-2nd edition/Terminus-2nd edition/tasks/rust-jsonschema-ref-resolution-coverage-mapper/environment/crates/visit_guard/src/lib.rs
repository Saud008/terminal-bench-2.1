use std::collections::BTreeSet;

#[derive(Debug, Default)]
pub struct VisitGuard {
    seen: BTreeSet<String>,
}

impl VisitGuard {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn enter(&mut self, doc_id: &str, _pointer: &str) -> bool {
        if self.seen.contains(doc_id) {
            return false;
        }
        self.seen.insert(doc_id.to_string());
        true
    }

    pub fn leave(&mut self, doc_id: &str, _pointer: &str) {
        self.seen.remove(doc_id);
    }
}
