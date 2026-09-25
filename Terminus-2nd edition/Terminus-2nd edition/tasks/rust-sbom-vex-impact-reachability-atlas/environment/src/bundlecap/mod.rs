use std::collections::HashMap;
use std::fs;

use crate::idcanon::canon::{collapse_packages, normalize_purl};
use crate::snapbuf::codec::{bump_run_seq, staging_digest, write_stage};
use crate::types::{AtlasStage, RawBundle, StageEdge, StagePackage, StageVex};

pub fn capture_bundle(bundle_path: &str, stage_path: &str) -> Result<(), String> {
    let raw_text = fs::read_to_string(bundle_path).map_err(|e| format!("read bundle: {e}"))?;
    let bundle: RawBundle =
        serde_json::from_str(&raw_text).map_err(|e| format!("parse bundle: {e}"))?;

    let collapsed = collapse_packages(&bundle.packages);
    let mut packages = Vec::new();
    for (norm, canonical_raw, name, version) in collapsed {
        packages.push(StagePackage {
            norm_purl: norm,
            canonical_raw,
            name,
            version,
        });
    }

    let purl_index: HashMap<String, (String, String)> = bundle
        .packages
        .iter()
        .map(|p| {
            (
                p.purl.clone(),
                (p.name.clone(), p.version.clone()),
            )
        })
        .collect();

    let mut edges = Vec::new();
    for e in &bundle.edges {
        let (fn_name, fn_ver) = purl_index
            .get(&e.from)
            .cloned()
            .unwrap_or_default();
        let (tn_name, tn_ver) = purl_index.get(&e.to).cloned().unwrap_or_default();
        edges.push(StageEdge {
            from: normalize_purl(&e.from, &fn_name, &fn_ver),
            to: normalize_purl(&e.to, &tn_name, &tn_ver),
            edge_kind: e.edge_kind.clone(),
        });
    }
    edges.sort_by(|a, b| a.from.cmp(&b.from).then(a.to.cmp(&b.to)));

    let mut vex = Vec::new();
    for v in &bundle.vex {
        let (pn, pv) = purl_index
            .get(&v.product_purl)
            .cloned()
            .unwrap_or_default();
        vex.push(StageVex {
            statement_id: v.statement_id.clone(),
            product_purl: normalize_purl(&v.product_purl, &pn, &pv),
            vuln_id: v.vuln_id.clone(),
            status: v.status.clone(),
            updated_at: v.updated_at.clone(),
            expires_at: v.expires_at.clone(),
        });
    }
    vex.sort_by(|a, b| a.statement_id.cmp(&b.statement_id));

    let capture_seq = bump_run_seq(&bundle.fingerprint)?;

    let mut stage = AtlasStage {
        bundle_id: bundle.bundle_id.clone(),
        fingerprint: bundle.fingerprint.clone(),
        ingest_seq: capture_seq,
        staging_digest: String::new(),
        packages,
        edges,
        vex,
        binaries: bundle.binaries.clone(),
        vulnerabilities: bundle.vulnerabilities.clone(),
    };
    stage.staging_digest = staging_digest(&stage);
    write_stage(stage_path, &stage)
}
