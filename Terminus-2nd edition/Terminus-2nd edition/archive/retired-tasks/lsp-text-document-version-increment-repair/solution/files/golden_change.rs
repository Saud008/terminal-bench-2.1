use anyhow::Result;
use docmodel::{changes_to_edits, working_text, ContentChange, Document};

use crate::staging::append_staging;

pub fn handle_did_change(doc: &mut Document, new_version: i32, changes: Vec<ContentChange>) -> Result<()> {
    if doc.last_change_version == Some(new_version) {
        return Ok(());
    }
    if new_version <= doc.version {
        return Ok(());
    }

    let base = working_text(doc);
    let edits = changes_to_edits(&changes, &base);
    append_staging(doc, edits);

    doc.version = new_version;
    doc.last_change_version = Some(new_version);
    Ok(())
}

pub fn peek_staging(doc: &Document) -> &[docmodel::StagedEdit] {
    &doc.staging
}
