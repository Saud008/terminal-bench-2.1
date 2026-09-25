use anyhow::Result;
use docmodel::{merge_staging, Document};

use crate::staging::clear_staging;

pub fn handle_did_open(uri: String, text: String, version: i32) -> Document {
    let mut doc = Document::new(uri, text);
    doc.version = version;
    doc
}

pub fn handle_did_close(doc: &mut Document) -> Result<()> {
    merge_staging(doc);
    clear_staging(doc);
    Ok(())
}
