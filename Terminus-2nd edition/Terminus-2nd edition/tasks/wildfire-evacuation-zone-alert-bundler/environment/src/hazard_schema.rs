use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoneSpec {
    pub zone_id: String,
    pub population: u32,
    pub polygon: Vec<Point>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FireSpec {
    pub fire_id: String,
    pub perimeter: Vec<Point>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShelterSpec {
    pub shelter_id: String,
    pub location: Point,
    pub capacity: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadNode {
    pub id: String,
    pub x: f64,
    pub y: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadEdge {
    pub from: String,
    pub to: String,
    pub km: f64,
    pub closed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadsSpec {
    pub nodes: Vec<RoadNode>,
    pub edges: Vec<RoadEdge>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicySpec {
    pub severity_ranks: BTreeMap<String, u32>,
    pub immediate_overlap: f64,
    pub urgent_overlap: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BindBundle {
    pub scenario: String,
    pub zones: Vec<ZoneSpec>,
    pub fires: Vec<FireSpec>,
    pub shelters: Vec<ShelterSpec>,
    pub roads: RoadsSpec,
    pub templates: BTreeMap<String, String>,
    pub policy: PolicySpec,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssignmentRow {
    pub zone_id: String,
    pub shelter_id: String,
    pub routed_km: f64,
    pub evacuees: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoneAlertRow {
    pub zone_id: String,
    pub severity: String,
    pub shelter_id: String,
    pub message: String,
    pub overlap_ratio: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WeaveLedger {
    pub run_id: String,
    pub scenario: String,
    pub assignments: Vec<AssignmentRow>,
    pub zone_alerts: Vec<ZoneAlertRow>,
    pub policy: PolicySpec,
    pub weave_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertBundle {
    pub zone_id: String,
    pub severity: String,
    pub shelter_id: String,
    pub message: String,
    pub overlap_ratio: f64,
    pub routed_km: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SealBundle {
    pub run_id: String,
    pub weave_digest: String,
    pub bundles: Vec<AlertBundle>,
    pub summary: BTreeMap<String, serde_json::Value>,
    pub bundle_digest: String,
}
