use crate::types::CorpusDoc;
use std::fs;
use std::path::Path;

pub fn load_jsonl(path: &Path) -> Result<Vec<CorpusDoc>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut docs = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let doc: CorpusDoc = serde_json::from_str(line).map_err(|e| e.to_string())?;
        docs.push(doc);
    }
    Ok(docs)
}

pub fn load_corpus_dir(dir: &Path) -> Result<Vec<CorpusDoc>, String> {
    let mut all = Vec::new();
    for entry in fs::read_dir(dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let p = entry.path();
        if p.extension().and_then(|s| s.to_str()) == Some("jsonl") {
            all.extend(load_jsonl(&p)?);
        }
    }
    all.sort_by(|a, b| a.doc_id.cmp(&b.doc_id));
    Ok(all)
}
