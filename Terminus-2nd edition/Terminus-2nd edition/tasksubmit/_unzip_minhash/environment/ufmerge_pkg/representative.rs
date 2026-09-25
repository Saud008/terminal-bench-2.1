pub fn pick_representative(doc_ids: &[String]) -> String {
    doc_ids.first().cloned().unwrap_or_default()
}
