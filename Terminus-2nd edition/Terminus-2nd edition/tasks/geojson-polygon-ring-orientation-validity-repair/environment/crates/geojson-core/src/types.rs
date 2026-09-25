use serde::{Deserialize, Serialize};

pub type Position = [f64; 2];
pub type Ring = Vec<Position>;
pub type PolygonCoords = Vec<Ring>;
pub type MultiPolygonCoords = Vec<PolygonCoords>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixtureInput {
    pub name: String,
    pub geometry: Geometry,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Geometry {
    Polygon { coordinates: PolygonCoords },
    MultiPolygon { coordinates: MultiPolygonCoords },
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct RepairStats {
    pub fixtures_read: u32,
    pub exterior_reversed: u32,
    pub interior_reversed: u32,
    pub duplicate_vertices_removed: u32,
    pub closing_vertices_normalized: u32,
    pub rings_reordered: u32,
    pub multipolygon_members: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixtureReport {
    pub name: String,
    pub geometry_type: String,
    pub coordinates: serde_json::Value,
    pub valid: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairReport {
    pub report_version: u32,
    pub valid: bool,
    pub fixtures: Vec<FixtureReport>,
    pub stats: RepairStats,
    pub repair_binding: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairSnapshot {
    pub sequence: u32,
    pub fixtures: Vec<FixtureReport>,
    pub stats: RepairStats,
}
