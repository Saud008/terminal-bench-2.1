//! Seal-stage bundle writer (verifier export path).

use crate::hazard_schema::{AlertBundle, SealBundle, WeaveLedger};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub fn seal_bundle(ledger: &WeaveLedger) -> SealBundle {
    let mut bundles: Vec<AlertBundle> = ledger
        .zone_alerts
        .iter()
        .map(|z| {
            let routed_km = ledger
                .assignments
                .iter()
                .find(|a| a.zone_id == z.zone_id)
                .map(|a| a.routed_km)
                .unwrap_or(0.0);
            AlertBundle {
                zone_id: z.zone_id.clone(),
                severity: z.severity.clone(),
                shelter_id: z.shelter_id.clone(),
                message: z.message.clone(),
                overlap_ratio: z.overlap_ratio,
                routed_km,
            }
        })
        .collect();
    bundles.sort_by(|a, b| a.zone_id.cmp(&b.zone_id));
    let mut summary = BTreeMap::new();
    summary.insert("bundle_count".into(), serde_json::json!(bundles.len()));
    summary.insert(
        "total_evacuees".into(),
        serde_json::json!(ledger.assignments.iter().map(|a| a.evacuees).sum::<u32>()),
    );
    let digest_body = serde_json::json!({ "bundles": bundles });
    let bundle_digest = format!("{:x}", Sha256::digest(digest_body.to_string().as_bytes()));
    SealBundle {
        run_id: ledger.run_id.clone(),
        weave_digest: String::new(),
        bundles,
        summary,
        bundle_digest,
    }
}
