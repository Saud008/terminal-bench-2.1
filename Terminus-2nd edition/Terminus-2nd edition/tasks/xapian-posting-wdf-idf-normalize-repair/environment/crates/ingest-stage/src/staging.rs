use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use xapi_tokenize::{positional_collapse, tokenize};
use xapi_types::document::Document;

pub fn write_staging(
    path: &Path,
    batch_raw: &str,
    docs: &[Document],
    written_before_index: bool,
) -> Result<(), String> {
    let mut terms = BTreeSet::new();
    for doc in docs {
        let collapsed = positional_collapse(&tokenize(&doc.body));
        for t in collapsed {
            terms.insert(t);
        }
    }
    let hash = Sha256::digest(batch_raw.as_bytes());
    let snapshot = serde_json::json!({
        "doc_count": docs.len(),
        "batch_sha256": hex::encode(hash),
        "terms": terms.into_iter().collect::<Vec<_>>(),
        "written_before_index": written_before_index,
    });
    let data = serde_json::to_string_pretty(&snapshot).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
