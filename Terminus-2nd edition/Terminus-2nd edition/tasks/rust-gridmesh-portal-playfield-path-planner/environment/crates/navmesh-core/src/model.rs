use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub type Q16 = i32;
pub type NodeId = String;

#[derive(Debug, Clone, Deserialize)]
pub struct MeshBundle {
    pub mesh_id: String,
    pub cells: Vec<CellSpec>,
    pub edges: Vec<EdgeSpec>,
    pub portals: Vec<PortalSpec>,
    pub offmesh: Vec<OffmeshSpec>,
    pub path_queries: Vec<PathQuerySpec>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CellSpec {
    pub id: String,
    pub gx: i32,
    pub gy: i32,
    pub walkable: bool,
    pub region: u16,
}

#[derive(Debug, Clone, Deserialize)]
pub struct EdgeSpec {
    pub from: String,
    pub to: String,
    pub cost_q16: Q16,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PortalSpec {
    pub id: String,
    pub from: String,
    pub to: String,
    pub cost_q16: Q16,
    pub require_region_match: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct OffmeshSpec {
    pub id: String,
    pub from: String,
    pub to: String,
    pub cost_q16: Q16,
    pub snap_radius_q16: Q16,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PathQuerySpec {
    pub id: String,
    pub from: String,
    pub to: String,
}

#[derive(Debug, Clone)]
pub struct CellNode {
    pub id: NodeId,
    pub gx: i32,
    pub gy: i32,
    pub walkable: bool,
    pub region: u16,
}

#[derive(Debug, Clone)]
pub struct Graph {
    pub nodes: HashMap<NodeId, CellNode>,
    pub adj: HashMap<NodeId, Vec<(NodeId, Q16)>>,
}

#[derive(Debug, Serialize)]
pub struct ValidateExport {
    pub mesh_id: String,
    pub seed: u64,
    pub ok: bool,
    pub errors: Vec<String>,
    pub islands: u32,
    pub links_checked: u32,
    pub portals_checked: u32,
}

#[derive(Debug, Serialize)]
pub struct PathExport {
    pub mesh_id: String,
    pub seed: u64,
    pub from: String,
    pub to: String,
    pub status: String,
    pub cost_q16: Q16,
    pub path: Vec<String>,
}
