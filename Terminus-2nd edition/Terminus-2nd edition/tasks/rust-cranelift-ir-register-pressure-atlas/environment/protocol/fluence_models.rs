use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub ledger_dir: String,
    pub bundle_dir: String,
    pub micron_ev_scale: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackgroundAnchor {
    pub energy_kev: f64,
    pub counts: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChannelIn {
    pub channel_id: String,
    pub energy_kev: f64,
    pub measured_counts: f64,
    pub width_kev: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VetoWindow {
    pub veto_id: String,
    pub lo_kev: f64,
    pub hi_kev: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub bundle_name: String,
    pub aperture_budget: i64,
    pub dwell_width_kev: f64,
    pub background_anchors: Vec<BackgroundAnchor>,
    pub channels: Vec<ChannelIn>,
    pub veto_windows: Vec<VetoWindow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FluenceChannel {
    pub channel_id: String,
    pub energy_q: f64,
    pub residual_counts: f64,
    pub width_q: f64,
    pub vetoed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FluenceLedger {
    pub accrual_epoch: u64,
    pub campaign_id: String,
    pub bundle: String,
    pub micron_ev_scale: i64,
    pub aperture_budget: i64,
    pub dwell_width_kev: f64,
    pub channels: Vec<FluenceChannel>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureRow {
    pub channel_id: String,
    pub residual_counts: f64,
    pub rank: usize,
    pub vetoed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureAtlas {
    pub campaign_id: String,
    pub effective_aperture: i64,
    pub channel_order: Vec<String>,
    pub max_occupancy: usize,
    pub peak_channel_id: String,
    pub spill_risk: bool,
    pub rows: Vec<ClosureRow>,
    pub closure_digest: String,
}
