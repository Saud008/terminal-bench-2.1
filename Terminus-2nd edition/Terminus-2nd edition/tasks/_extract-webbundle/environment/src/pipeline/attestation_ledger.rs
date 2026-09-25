use crate::wble_reader::{read_bundle_dir, ExchangeRecord, WbleBundle};
use crate::mime_guard::{find_content_type, mime_allowed};
use crate::variant_pick::resolve_duplicates;
use crate::ihsh_digest::{exchange_digest, hash_matches};
use crate::scope_guard::scope_violations;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use crate::url_norm::canonical_url;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StagedExchange {
    pub bundle_id: String,
    pub variant_id: u32,
    pub url: String,
    pub canonical_url: String,
    pub status: u16,
    pub headers: Vec<(String, String)>,
    pub body_sha256: String,
    pub hash_ok: bool,
    pub in_scope: bool,
    pub ctype_ok: bool,
}

pub fn ingest_bundles(bundle_dir: &Path, staging_path: &Path) -> Result<(), String> {
    let bundles = read_bundle_dir(bundle_dir).map_err(|_| "bundle read failed".to_string())?;
    let mut rows = Vec::new();
    for bundle in bundles {
        rows.extend(stage_bundle(&bundle)?);
    }
    rows.sort_by(|a, b| a.url.cmp(&b.url));
    let lines: Vec<String> = rows
        .into_iter()
        .map(|r| serde_json::to_string(&r).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    fs::write(staging_path, format!("{}
", lines.join("
"))).map_err(|e| e.to_string())
}

fn stage_bundle(bundle: &WbleBundle) -> Result<Vec<StagedExchange>, String> {
    let resolved = resolve_duplicates(bundle.exchanges.clone());
    let mut out = Vec::new();
    for (idx, ex) in resolved.iter().enumerate() {
        let canon = canonical_url(&ex.url);
        let digest = exchange_digest(&canon, ex.status, &ex.headers, &ex.body);
        let expected = bundle.integrity_hashes.get(idx).copied();
        let hash_ok = expected.map(|e| hash_matches(&e, &canon, ex.status, &ex.headers, &ex.body)).unwrap_or(true);
        let ctype = find_content_type(&ex.headers).unwrap_or_default();
        let ctype_ok = mime_allowed(&ctype, &bundle.allowed_mimes);
        let in_scope = !scope_violations(&ex.url, &bundle.scopes);
        out.push(StagedExchange {
            bundle_id: bundle.bundle_id.clone(),
            variant_id: ex.variant_id,
            url: ex.url.clone(),
            canonical_url: canon,
            status: ex.status,
            headers: ex.headers.clone(),
            body_sha256: hex::encode(digest),
            hash_ok,
            in_scope,
            ctype_ok,
        });
    }
    Ok(out)
}

pub fn read_staging(path: &Path) -> Result<Vec<StagedExchange>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}

mod hex {
    pub fn encode(bytes: [u8; 32]) -> String {
        bytes.iter().map(|b| format!("{b:02x}")).collect()
    }
}
