use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub hub_latch_dir: String,
    pub scan_ledger_dir: String,
    pub route_lattice_dir: String,
    pub output_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HubLatch {
    pub hub_id: String,
    pub topology_revision: u32,
    pub belts: Vec<BeltSpec>,
    pub flights: Vec<FlightSpec>,
    pub connections: Vec<ConnectionSpec>,
    pub outages: Vec<OutageSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BeltSpec {
    pub belt_id: String,
    pub priority: u32,
    pub station_code: String,
    pub target_flight_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlightSpec {
    pub flight_id: String,
    pub dep_minute: u64,
    pub arr_minute: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionSpec {
    pub inbound_flight: String,
    pub outbound_flight: String,
    pub min_connect_minutes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutageSpec {
    pub station_code: String,
    pub start_minute: u64,
    pub end_minute: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanRow {
    pub bag_tag: String,
    pub scan_seq: u64,
    pub belt_id: String,
    pub station_code: String,
    pub scan_minute: u64,
    pub relay_pass: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteRow {
    pub bag_tag: String,
    pub scan_seq: u64,
    pub belt_id: String,
    pub station_code: String,
    pub scan_minute: u64,
    pub target_flight_id: String,
    pub connection_ok: bool,
    pub outage_suppressed: bool,
    pub misroute_cause: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasDoc {
    pub hub_id: String,
    pub topology_revision: u32,
    pub route_row_count: u32,
    pub misroute_count: u32,
    pub suppressed_count: u32,
    pub cause_histogram: BTreeMap<String, u32>,
    pub audit_digest: String,
}
