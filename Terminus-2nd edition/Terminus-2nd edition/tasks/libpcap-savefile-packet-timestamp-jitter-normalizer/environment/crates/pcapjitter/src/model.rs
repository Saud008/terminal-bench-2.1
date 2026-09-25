use serde::{Deserialize, Serialize};

pub const MAGIC_LE: u32 = 0xa1b2c3d4;
pub const MAGIC_BE: u32 = 0xd4c3b2a1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PacketMeta {
    pub index: u32,
    pub ts_sec: u32,
    pub ts_usec: u32,
    pub incl_len: u32,
    pub orig_len: u32,
    pub raw_ts_us: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StagingFile {
    pub source: String,
    pub snaplen: u32,
    pub network: u32,
    pub packets: Vec<PacketMeta>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TimelinePacket {
    pub index: u32,
    pub norm_ns: u64,
    pub incl_len: u32,
    pub orig_len: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TimelineStats {
    pub gap_count: u64,
    pub trunc_penalty_total_ns: u64,
    pub packet_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TimelineExport {
    pub packets: Vec<TimelinePacket>,
    pub stats: TimelineStats,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GapRow {
    pub seq: u64,
    pub after_index: u32,
    pub gap_ns: u64,
    pub prev_norm_ns: u64,
    pub next_norm_ns: u64,
}

#[derive(Debug, Clone, Copy)]
pub struct Policy {
    pub window_us: u64,
    pub gap_threshold_ns: u64,
    pub trunc_ns_per_byte: u64,
}

impl Default for Policy {
    fn default() -> Self {
        Self {
            window_us: 5000,
            gap_threshold_ns: 1_000_000_000,
            trunc_ns_per_byte: 100,
        }
    }
}

impl Policy {
    pub fn from_env() -> Self {
        let mut p = Self::default();
        if let Ok(v) = std::env::var("PCAP_JITTER_WINDOW_US") {
            if let Ok(n) = v.parse::<u64>() {
                if n > 0 {
                    p.window_us = n;
                }
            }
        }
        if let Ok(v) = std::env::var("PCAP_JITTER_GAP_NS") {
            if let Ok(n) = v.parse::<u64>() {
                if n > 0 {
                    p.gap_threshold_ns = n;
                }
            }
        }
        if let Ok(v) = std::env::var("PCAP_JITTER_TRUNC_NS") {
            if let Ok(n) = v.parse::<u64>() {
                if n > 0 {
                    p.trunc_ns_per_byte = n;
                }
            }
        }
        p
    }
}

pub fn penalty_ns(pkt: &PacketMeta, policy: Policy) -> u64 {
    if pkt.incl_len >= pkt.orig_len {
        return 0;
    }
    (pkt.orig_len - pkt.incl_len) as u64 * policy.trunc_ns_per_byte
}
