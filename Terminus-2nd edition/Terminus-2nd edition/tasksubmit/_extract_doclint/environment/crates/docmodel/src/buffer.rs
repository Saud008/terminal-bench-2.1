use crate::apply::apply_edits;
use crate::types::Document;

pub fn working_text(doc: &Document) -> String {
    if doc.staging.is_empty() {
        return doc.text.clone();
    }
    apply_edits(&doc.text, &doc.staging)
}

pub fn merge_staging(doc: &mut Document) {
    if doc.staging.is_empty() {
        return;
    }
    doc.text = working_text(doc);
    doc.staging.clear();
}
