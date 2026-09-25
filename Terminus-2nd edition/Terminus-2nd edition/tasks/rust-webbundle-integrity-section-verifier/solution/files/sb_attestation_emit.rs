use serde::Serialize;
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

pub fn export_evidence(staging_path: &Path, _bundle_meta_path: &Path, out_path: &Path) -> Result<(), String> {
    let staged = crate::attestation_ledger::read_staging(staging_path)?;
    let mut bundles_map: BTreeMap<String, BundleEvidence> = BTreeMap::new();
    let mut hash_fail = 0u32;
    let mut ctype_fail = 0u32;
    let mut scope_fail = 0u32;
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
        if !row.in_scope {
            scope_fail += 1;
            entry.findings.push(Finding {
                kind: "scope_violation".into(),
                bundle_id: row.bundle_id.clone(),
                url: row.canonical_url.clone(),
                detail: "url outside declared scope prefixes".into(),
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
    }
    let mut bundles: Vec<BundleEvidence> = bundles_map.into_values().collect();
    for b in &mut bundles {
        b.exchanges.sort_by(|a, b| a.canonical_url.cmp(&b.canonical_url));
    }
    bundles.sort_by(|a, b| a.bundle_id.cmp(&b.bundle_id));
    let finding_count = hash_fail + scope_fail + ctype_fail;
    let report = EvidenceReport {
        bundles,
        totals: Totals {
            exchange_count: staged.len() as u32,
            verified_count: verified,
            finding_count,
            hash_failures: hash_fail,
            scope_violations: scope_fail,
            ctype_violations: ctype_fail,
        },
    };
    let json = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}
