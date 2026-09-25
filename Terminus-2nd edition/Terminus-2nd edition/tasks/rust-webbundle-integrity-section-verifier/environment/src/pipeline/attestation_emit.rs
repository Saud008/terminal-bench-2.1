use crate::scope_guard::scope_violations;
use serde::Serialize;
use crate::attestation_ledger::StagedExchange;
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct Finding {
    pub kind: String,
    pub bundle_id: String,
    pub url: String,
    pub detail: String,
}

#[derive(Debug, Serialize)]
pub struct EvidenceReport {
    pub bundles: Vec<BundleEvidence>,
    pub totals: Totals,
}

#[derive(Debug, Serialize)]
pub struct BundleEvidence {
    pub bundle_id: String,
    pub exchanges: Vec<ExchangeEvidence>,
    pub findings: Vec<Finding>,
}

#[derive(Debug, Serialize)]
pub struct ExchangeEvidence {
    pub canonical_url: String,
    pub status: u16,
    pub hash_ok: bool,
    pub in_scope: bool,
    pub ctype_ok: bool,
}

#[derive(Debug, Serialize)]
pub struct Totals {
    pub exchange_count: u32,
    pub verified_count: u32,
    pub finding_count: u32,
    pub hash_failures: u32,
    pub scope_violations: u32,
    pub ctype_violations: u32,
}

pub fn export_evidence(staging_path: &Path, bundle_meta_path: &Path, out_path: &Path) -> Result<(), String> {
    let staged = crate::attestation_ledger::read_staging(staging_path)?;
    let meta: BTreeMap<String, BundleMeta> = if bundle_meta_path.exists() {
        serde_json::from_str(&fs::read_to_string(bundle_meta_path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?
    } else {
        BTreeMap::new()
    };
    let mut bundles_map: BTreeMap<String, BundleEvidence> = BTreeMap::new();
    let mut hash_fail = 0u32;
    let mut ctype_fail = 0u32;
    let mut verified = 0u32;
    for row in &staged {
        let entry = bundles_map.entry(row.bundle_id.clone()).or_insert_with(|| BundleEvidence {
            bundle_id: row.bundle_id.clone(),
            exchanges: Vec::new(),
            findings: Vec::new(),
        });
        entry.exchanges.push(ExchangeEvidence {
            canonical_url: row.canonical_url.clone(),
            status: row.status,
            hash_ok: row.hash_ok,
            in_scope: row.in_scope,
            ctype_ok: row.ctype_ok,
        });
        if row.hash_ok && row.in_scope && row.ctype_ok {
            verified += 1;
        }
        if !row.hash_ok {
            hash_fail += 1;
            entry.findings.push(Finding {
                kind: "hash_mismatch".into(),
                bundle_id: row.bundle_id.clone(),
                url: row.canonical_url.clone(),
                detail: "integrity section digest mismatch".into(),
            });
        }
        if !row.ctype_ok {
            ctype_fail += 1;
            entry.findings.push(Finding {
                kind: "ctype_violation".into(),
                bundle_id: row.bundle_id.clone(),
                url: row.canonical_url.clone(),
                detail: "content-type not allowed for bundle".into(),
            });
        }
        if let Some(m) = meta.get(&row.bundle_id) {
            if scope_violations(&row.url, &m.scopes) && row.in_scope {
                entry.findings.push(Finding {
                    kind: "scope_violation".into(),
                    bundle_id: row.bundle_id.clone(),
                    url: row.canonical_url.clone(),
                    detail: "url outside declared scope prefixes".into(),
                });
            }
        }
    }
    let exchange_count = staged.len() as u32;
    let finding_count = hash_fail + ctype_fail;
    let report = EvidenceReport {
        bundles: bundles_map.into_values().collect(),
        totals: Totals {
            exchange_count,
            verified_count: verified,
            finding_count,
            hash_failures: hash_fail,
            scope_violations: 0,
            ctype_violations: ctype_fail,
        },
    };
    let json = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}

#[derive(Debug, serde::Deserialize)]
struct BundleMeta {
    scopes: Vec<String>,
}
