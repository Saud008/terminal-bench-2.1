pub fn pick_representative(doc_ids: &[String]) -> String {
    doc_ids.iter().min().cloned().unwrap_or_default()
}
