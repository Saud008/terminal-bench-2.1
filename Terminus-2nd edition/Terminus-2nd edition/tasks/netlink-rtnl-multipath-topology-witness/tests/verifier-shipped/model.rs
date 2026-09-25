use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct RawHop {
    pub ifindex: i32,
    pub weight_raw: u8,
    pub gateway: Option<Vec<u8>>,
    pub gw_family: u8,
}

#[derive(Debug, Clone)]
pub struct RawRoute {
    pub family: u8,
    pub table_id: u32,
    pub dst: Vec<u8>,
    pub dst_plen: u8,
    pub priority: Option<u32>,
    pub table_attr: Option<u32>,
    pub nh_id_hint: Option<u32>,
    pub gateway: Option<Vec<u8>>,
    pub oif: Option<u32>,
    pub multipath: Vec<RawHop>,
    pub metrics: BTreeMap<String, u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NexthopOut {
    pub id: u32,
    pub ifindex: i32,
    pub weight: u32,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub gateway: Option<String>,
    #[serde(skip_serializing_if = "BTreeMap::is_empty", default)]
    pub metrics: BTreeMap<String, u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteOut {
    pub family: String,
    pub table: u32,
    pub dst: String,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub priority: Option<u32>,
    pub nexthops: Vec<NexthopOut>,
}

#[derive(Debug, Serialize)]
pub struct ExportDoc {
    pub pipeline_version: u32,
    pub seed: String,
    pub routes: Vec<RouteOut>,
    pub export_digest: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BindSnapshotDoc {
    pub version: u32,
    pub seed: String,
    pub source_dump: String,
    pub routes: Vec<RouteOut>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NhSnapshotDoc {
    pub version: u32,
    pub seed: String,
    pub source_dump: String,
    pub bind_snapshot: String,
    pub snapshot_routes: Vec<RouteOut>,
    pub routes: Vec<RouteOut>,
}
