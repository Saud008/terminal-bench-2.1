use crate::mod_f::{chrono_findings, lab_window_findings};
use crate::custody_types::{
    IntegrityFinding, DossierReport, DossierSummary, RegisterLedger, LineageEdge,
    VaultLedger, TransferEvent,
};
use crate::mod_e::alias_findings;
use crate::mod_b::{build_edges, lineage_gap};
use crate::mod_d::location_findings;
use crate::mod_c::seal_findings;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

fn count_code(rows: &[IntegrityFinding], code: &str) -> u64 {
    rows.iter().filter(|r| r.code == code).count() as u64
}

pub fn compile(
    vault: &VaultLedger,
    ledger: &RegisterLedger,
    catalog_path: &str,
) -> Result<DossierReport, String> {
    let transfers = &ledger.transfers;
    let mut broken = Vec::new();
    broken.extend(seal_findings(&[]));
    broken.extend(
        location_findings(catalog_path, transfers).unwrap_or_default(),
    );
    broken.extend(chrono_findings(transfers));
    broken.extend(lab_window_findings(transfers));
    broken.extend(alias_findings(&ledger.exhibit_aliases));
    let evidence_items: BTreeSet<String> =
        transfers.iter().map(|t| t.evidence_id.clone()).collect();
    for eid in &evidence_items {
        if lineage_gap(eid, transfers) {
            broken.push(IntegrityFinding {
                evidence_id: eid.clone(),
                code: "lineage_gap".into(),
                detail: "custody hop discontinuity".into(),
            });
        }
    }
    broken.sort_by(|a, b| {
        a.evidence_id
            .cmp(&b.evidence_id)
            .then(a.code.cmp(&b.code))
    });
    let broken_set: BTreeSet<String> =
        broken.iter().map(|b| b.evidence_id.clone()).collect();
    let edges: Vec<LineageEdge> = build_edges(transfers);
    let summary = DossierSummary {
        intact_items: (evidence_items.len() - broken_set.len()) as u64,
        defect_items: broken_set.len() as u64,
        seal_breaks: count_code(&broken, "seal_break"),
        location_invalid: count_code(&broken, "location_invalid"),
        chronology_violation: count_code(&broken, "chronology_violation"),
        lineage_gap: count_code(&broken, "lineage_gap"),
        alias_collision: count_code(&broken, "alias_collision"),
    };
    let body = serde_json::json!({
        "case_id": vault.case_id,
        "bundle_id": vault.bundle_id,
        "run_seq": vault.run_seq,
        "intact_items": summary.intact_items,
        "defect_items": summary.defect_items,
    });
    let digest = hex::encode(Sha256::digest(
        serde_json::to_string(&body).unwrap_or_default().as_bytes(),
    ));
    Ok(DossierReport {
        case_id: vault.case_id.clone(),
        bundle_id: vault.bundle_id.clone(),
        run_seq: vault.run_seq,
        evidence_items: evidence_items.into_iter().collect(),
        lineage_edges: edges,
        integrity_findings: broken,
        summary,
        custody_digest: digest,
    })
}

pub fn reconcile(
    vault: &VaultLedger,
    bundle_transfers: &[TransferEvent],
    aliases: &[crate::custody_types::ExhibitAlias],
) -> Result<RegisterLedger, String> {
    let ledger = RegisterLedger {
        case_id: vault.case_id.clone(),
        bundle_id: vault.bundle_id.clone(),
        ledger_seq: vault.run_seq,
        exhibit_aliases: aliases.to_vec(),
        transfers: bundle_transfers.to_vec(),
    };
    std::fs::create_dir_all("/app/var").map_err(|e| e.to_string())?;
    std::fs::write(
        "/app/var/exhibit-register.json",
        serde_json::to_string_pretty(&ledger).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(ledger)
}
