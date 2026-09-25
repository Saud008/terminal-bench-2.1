use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AisRow {
    pub seq: u32,
    pub mmsi: u64,
    pub ts_epoch: i64,
    pub lat: f64,
    pub lon: f64,
    pub sog: f64,
    pub draught: f64,
    pub station: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FeedStats {
    pub raw_rows: u64,
    pub after_mmsi_dedupe: u64,
    pub after_burst: u64,
    pub out_of_order: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SnapshotFile {
    pub source: String,
    pub points: Vec<AisRow>,
    pub feed_stats: FeedStats,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VoyageLeg {
    pub leg_id: String,
    pub mmsi: u64,
    pub start_ts: String,
    pub end_ts: String,
    pub point_count: u64,
    pub start_port: String,
    pub end_port: String,
    pub ports: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AnomalyCounts {
    pub impossible_speed: u64,
    pub duplicate_mmsi: u64,
    pub burst_duplicate: u64,
    pub out_of_order: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VoyageAtlas {
    pub voyage_legs: Vec<VoyageLeg>,
    pub anomalies: AnomalyCounts,
    pub leg_chain_digest: String,
}

#[derive(Debug, Clone, Copy)]
pub struct Policy {
    pub mmsi_dedupe_sec: i64,
    pub burst_ms: i64,
    pub max_sog_knots: f64,
    pub draught_delta_m: f64,
    pub max_gap_hours: f64,
}

impl Default for Policy {
    fn default() -> Self {
        Self {
            mmsi_dedupe_sec: 2,
            burst_ms: 500,
            max_sog_knots: 45.0,
            draught_delta_m: 0.5,
            max_gap_hours: 12.0,
        }
    }
}

impl Policy {
    pub fn from_env() -> Self {
        let mut p = Self::default();
        if let Ok(v) = std::env::var("AIS_MMSI_DEDUPE_SEC") {
            if let Ok(n) = v.parse::<i64>() {
                if n >= 0 {
                    p.mmsi_dedupe_sec = n;
                }
            }
        }
        if let Ok(v) = std::env::var("AIS_BURST_MS") {
            if let Ok(n) = v.parse::<i64>() {
                if n >= 0 {
                    p.burst_ms = n;
                }
            }
        }
        if let Ok(v) = std::env::var("AIS_MAX_SOG_KNOTS") {
            if let Ok(n) = v.parse::<f64>() {
                if n > 0.0 {
                    p.max_sog_knots = n;
                }
            }
        }
        if let Ok(v) = std::env::var("AIS_DRAUGHT_DELTA_M") {
            if let Ok(n) = v.parse::<f64>() {
                if n > 0.0 {
                    p.draught_delta_m = n;
                }
            }
        }
        if let Ok(v) = std::env::var("AIS_MAX_GAP_HOURS") {
            if let Ok(n) = v.parse::<f64>() {
                if n > 0.0 {
                    p.max_gap_hours = n;
                }
            }
        }
        p
    }
}

pub fn round6(v: f64) -> f64 {
    (v * 1_000_000.0).round() / 1_000_000.0
}

pub fn epoch_to_rfc3339(epoch: i64) -> String {
    let dt = time::OffsetDateTime::UNIX_EPOCH + time::Duration::seconds(epoch);
    dt.format(&time::format_description::well_known::Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".to_string())
}
