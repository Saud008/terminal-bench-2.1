    pub fn merge_with_pending(&mut self, merge_key: &str, incoming: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
        let mut pending = self.take_fragments(merge_key);
        pending.extend(incom