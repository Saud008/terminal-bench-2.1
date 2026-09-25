use docmodel::{Document, StagedEdit};

pub fn append_staging(doc: &mut Document, edits: Vec<StagedEdit>) {
    doc.staging.extend(edits);
}

pub fn clear_staging(doc: &mut Document) {
    doc.staging.clear();
}

pub fn staging_len(doc: &Document) -> usize {
    doc.staging.len()
}
