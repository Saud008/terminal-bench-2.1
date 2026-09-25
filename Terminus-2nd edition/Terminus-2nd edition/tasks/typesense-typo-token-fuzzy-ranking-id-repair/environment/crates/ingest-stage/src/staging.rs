use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};
use ts_types::document::Document;
use ts_tokenize::token_dedupe::index_terms;

pub fn write_staging(
    path: &Path,
    raw_batch: &str,
    docs: &[Document],
    written_before_index: bool,
) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let mut terms = BTreeSet::new();
    for doc in docs {
        for t in index_terms(&doc.searchable_text()) {
            terms.insert(t);
        }
    }
    let digest = Sha256::digest(raw_batch.as_bytes());
    let snap = serde_json::json!({
        "doc_count": docs.len(),
        "batch_sha256": hex::encode(digest),
        "terms": terms.into_iter().collect::<Vec<_>>(),
        "written_before_index": written_before_index,
    });
    fs::write(path, format!("{}\n", snap)).map_err(|e| e.to_string())
}
