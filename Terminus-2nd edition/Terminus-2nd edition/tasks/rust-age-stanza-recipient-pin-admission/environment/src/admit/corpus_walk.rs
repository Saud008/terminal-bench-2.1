use crate::fingerprint::stanza_fp;
use crate::parse::header_scan::{self, ParsedFile};
use std::fs;
use std::path::Path;

/// Ingest path: walk *.age headers from a corpus directory into parsed rows.
pub fn walk_corpus(dir: &Path) -> Result<Vec<ParsedFile>, String> {
    ingest_corpus(dir)
}

pub fn ingest_corpus(dir: &Path) -> Result<Vec<ParsedFile>, String> {
    let mut out = Vec::new();
    let rd = fs::read_dir(dir).map_err(|e| e.to_string())?;
    for ent in rd {
        let ent = ent.map_err(|e| e.to_string())?;
        let path = ent.path();
        if path.extension().and_then(|s| s.to_str()) != Some("age") {
            continue;
        }
        let bytes = fs::read(&path).map_err(|e| e.to_string())?;
        let stem = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();
        let rel = path.to_string_lossy().to_string();
        let mut parsed = header_scan::parse_age_header(&bytes, &stem, &rel);
        for st in &mut parsed.stanzas {
            st.fingerprint = stanza_fp::stanza_fingerprint(&st.type_name, &st.args);
        }
        out.push(parsed);
    }
    out.sort_by(|a, b| a.rel_path.cmp(&b.rel_path));
    Ok(out)
}
