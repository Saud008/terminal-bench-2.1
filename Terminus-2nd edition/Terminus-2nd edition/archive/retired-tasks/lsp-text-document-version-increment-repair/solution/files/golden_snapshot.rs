use anyhow::Result;
use docdiag::compute_diagnostics;
use docmodel::{merge_staging, Document};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct ExportSnapshot {
    pub uri: String,
    pub version: i32,
    pub text: String,
    pub diagnostics: docdiag::DiagnosticCounts,
    pub staging_pending: usize,
}

pub fn export_snapshot(doc: &mut Document) -> Result<ExportSnapshot> {
    merge_staging(doc);
    let text = doc.text.clone();
    let diagnostics = compute_diagnostics(&text);
    Ok(ExportSnapshot {
        uri: doc.uri.clone(),
        version: doc.version,
        text,
        diagnostics,
        staging_pending: doc.staging.len(),
    })
}
