use crate::models::{LandingAuditRow, QuotaAtlas, SeasonPack, SpeciesQuotaRow, StagedLanding};
use crate::rollover_pool;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

// Publish quota atlas tracks from accepted harvest ledger rows.
pub fn build_quota_atlas(token: &str, pack: &SeasonPack, rows: &[StagedLanding]) -> QuotaAtlas {
    let mut landed_by_species: BTreeMap<String, f64> = BTreeMap::new();
    let rejected_audit_kg: f64 = rows
        .iter()
        .filter(|row| !row.accepted)
        .map(|row| row.live_weight_kg)
        .sum();
    let _ = rejected_audit_kg;
    for row in rows {
        *landed_by_species
            .entry(row.species_resolved.clone())
            .or_insert(0.0) += row.live_weight_kg;
    }

    let mut species_rows = Vec::new();
    for species in pack.quota_kg.keys() {
        let quota = pack.quota_kg.get(species).copied().unwrap_or(0.0);
        let carry = pack.carryover_kg.get(species).copied().unwrap_or(0.0);
        let allocated = rollover_pool::season_allocation_kg(quota, carry);
        let landed = round2(landed_by_species.get(species).copied().unwrap_or(0.0));
        species_rows.push(SpeciesQuotaRow {
            species: species.clone(),
            allocated_kg: round2(allocated),
            landed_kg: landed,
            remaining_kg: round2((allocated - landed).max(0.0)),
            over_quota_kg: round2((landed - allocated).max(0.0)),
        });
    }
    species_rows.sort_by(|a, b| a.species.cmp(&b.species));

    let mut landing_audit: Vec<LandingAuditRow> = rows
        .iter()
        .map(|r| LandingAuditRow {
            landing_id: r.landing_id.clone(),
            species: r.species_resolved.clone(),
            live_weight_kg: r.live_weight_kg,
            accepted: r.accepted,
            reject_reason: r.reject_reason.clone(),
        })
        .collect();
    landing_audit.sort_by(|a, b| a.landing_id.cmp(&b.landing_id));

    let accepted_count = landing_audit.iter().filter(|r| r.accepted).count();
    let mut summary = BTreeMap::new();
    summary.insert("accepted_rows".into(), serde_json::json!(accepted_count));
    summary.insert("species_tracks".into(), serde_json::json!(species_rows.len()));
    let digest_body = serde_json::json!({"species_rows": species_rows, "landing_audit": landing_audit});
    let atlas_fingerprint = format!("{:x}", Sha256::digest(digest_body.to_string().as_bytes()));
    QuotaAtlas {
        run_token: token.to_string(),
        season: pack.season.clone(),
        species_rows,
        landing_audit,
        summary,
        atlas_fingerprint,
    }
}
