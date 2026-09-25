use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LandingRow {
    pub landing_id: String,
    pub vessel_id: String,
    pub species_code: String,
    pub product_weight_kg: f64,
    pub landed_at: String,
    pub lat: f64,
    pub lon: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PermitSpec {
    pub valid_from: String,
    pub valid_until: String,
    pub species: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosedArea {
    pub area_id: String,
    pub min_lat: f64,
    pub max_lat: f64,
    pub min_lon: f64,
    pub max_lon: f64,
    pub closed_from: String,
    pub closed_until: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeasonPack {
    pub season: String,
    pub species_aliases: BTreeMap<String, Vec<String>>,
    pub conversion_factors: BTreeMap<String, f64>,
    pub quota_kg: BTreeMap<String, f64>,
    pub carryover_kg: BTreeMap<String, f64>,
    pub closed_areas: Vec<ClosedArea>,
    pub permits: BTreeMap<String, PermitSpec>,
    pub landings: Vec<LandingRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StagedLanding {
    pub landing_id: String,
    pub vessel_id: String,
    pub species_raw: String,
    pub species_resolved: String,
    pub product_weight_kg: f64,
    pub live_weight_kg: f64,
    pub landed_at: String,
    pub accepted: bool,
    pub reject_reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerHeader {
    pub run_token: String,
    pub season: String,
    pub row_count: usize,
    pub ledger_fingerprint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpeciesQuotaRow {
    pub species: String,
    pub allocated_kg: f64,
    pub landed_kg: f64,
    pub remaining_kg: f64,
    pub over_quota_kg: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LandingAuditRow {
    pub landing_id: String,
    pub species: String,
    pub live_weight_kg: f64,
    pub accepted: bool,
    pub reject_reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaAtlas {
    pub run_token: String,
    pub season: String,
    pub species_rows: Vec<SpeciesQuotaRow>,
    pub landing_audit: Vec<LandingAuditRow>,
    pub summary: BTreeMap<String, serde_json::Value>,
    pub atlas_fingerprint: String,
}
