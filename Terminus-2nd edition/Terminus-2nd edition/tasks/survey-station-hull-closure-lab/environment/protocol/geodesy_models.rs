use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub lattice_dir: String,
    pub bundle_dir: String,
    pub microdegree_scale: i64,
    pub datum_offset: DatumOffset,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatumOffset {
    pub lon: f64,
    pub lat: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StationIn {
    pub station_id: String,
    pub vertices: Vec<[f64; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub bundle_name: String,
    pub stations: Vec<StationIn>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatticeStation {
    pub station_id: String,
    pub residual_vertices: Vec<[f64; 2]>,
    pub quantized_vertices: Vec<[f64; 2]>,
    pub min_x: f64,
    pub min_y: f64,
    pub max_x: f64,
    pub max_y: f64,
    pub residual_area_u64: u64,
    pub vertex_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatticeArtifact {
    pub materialize_generation: u64,
    pub campaign_id: String,
    pub bundle: String,
    pub microdegree_scale: i64,
    pub stations: Vec<LatticeStation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureRow {
    pub station_id: String,
    pub residual_area_u64: u64,
    pub vertex_count: usize,
    pub rank: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureSummary {
    pub total_stations: usize,
    pub wrap_parts: usize,
    pub max_area: u64,
    pub min_area: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureAtlas {
    pub campaign_id: String,
    pub rows: Vec<ClosureRow>,
    pub summary: ClosureSummary,
    pub closure_digest: String,
}
