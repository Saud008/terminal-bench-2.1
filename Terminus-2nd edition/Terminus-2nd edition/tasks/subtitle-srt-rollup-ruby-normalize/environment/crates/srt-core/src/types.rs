use serde::{Deserialize, Serialize};

pub const RUBY_SHIFT_MS: u32 = 250;
pub const ROLLUP_GAP_MS: u32 = 120;
pub const EXPORT_FORMAT: &str = "srt-normalized-v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RubySegment {
    pub base: String,
    pub reading: String,
    pub start_ms: u32,
    pub end_ms: u32,
}

#[derive(Debug, Clone)]
pub struct ParsedCue {
    pub source_index: u32,
    pub start_ms: u32,
    pub end_ms: u32,
    pub lines: Vec<String>,
    pub has_an8: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExportCue {
    pub index: u32,
    pub source_index: u32,
    pub start_ms: u32,
    pub end_ms: u32,
    pub text: String,
    pub ruby_segments: Vec<RubySegment>,
    pub rolled_up: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExportStats {
    pub parsed: u32,
    pub exported: u32,
    pub overlap_trims: u32,
    pub rollup_removals: u32,
    pub ruby_shifts: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExportDoc {
    pub fixture: String,
    pub seed: String,
    pub seed_offset_ms: u32,
    pub format: String,
    pub cues: Vec<ExportCue>,
    pub stats: ExportStats,
}

pub fn seed_offset_ms(seed: &str) -> u32 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in seed.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    50 + (hash % 450) as u32
}
