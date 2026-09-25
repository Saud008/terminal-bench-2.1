use anyhow::Result;
use docmodel::{changes_to_edits, ContentChange, Document, StagedEdit};

use crate::staging::append_staging;

pub fn handle_did_change(doc: &mut Document, new_version: i32, changes: Vec<ContentChange>) -> Result<()> {
    doc.version = new_version;

    let edits = changes_to_edits(&changes, &doc.text);
    append_staging(doc, edits);

    doc.last_change_version = Some(new_version);
    Ok(())
}

pub fn peek_staging(doc: &Document) -> &[StagedEdit] {
    &doc.staging
}
