use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::ruby::RubyCue;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct NormalizeSnapshot {
    pub version: u32,
    pub fixture: String,
    pub seed: String,
    pub input_path: String,
    pub input_digest: String,
    pub seed_offset_ms: u32,
    pub parsed_count: u32,
    pub overlap_trims: u32,
    pub ruby_shifts: u32,
    pub cues: Vec<RubyCue>,
}

pub fn snapshot_dir(fixture: &str, seed: &str) -> PathBuf {
    PathBuf::from("/app/state/srtctl").join(format!("{fixture}-{seed}"))
}

pub fn snapshot_path(fixture: &str, seed: &str) -> PathBuf {
    snapshot_dir(fixture, seed).join("normalize-snapshot.json")
}

pub fn input_digest(path: &Path) -> String {
    let bytes = fs::read(path).expect("read fixture for digest");
    format!("{:016x}", fnv1a64_bytes(&bytes))
}

fn fnv1a64_bytes(bytes: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

pub fn write_snapshot(
    path: &Path,
    fixture: &str,
    seed: &str,
    seed_offset_ms: u32,
    parsed_count: u32,
    overlap_trims: u32,
    ruby_shifts: u32,
    cues: Vec<RubyCue>,
) -> PathBuf {
    let out = snapshot_path(fixture, seed);
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent).expect("create snapshot dir");
    }
    let payload = NormalizeSnapshot {
        version: 1,
        fixture: fixture.to_string(),
        seed: seed.to_string(),
        input_path: path.to_string_lossy().into_owned(),
        input_digest: input_digest(path),
        seed_offset_ms,
        parsed_count,
        overlap_trims,
        ruby_shifts,
        cues,
    };
    let json = serde_json::to_string_pretty(&payload).expect("serialize snapshot");
    fs::write(&out, format!("{json}\n")).expect("write snapshot");
    out
}

pub fn read_snapshot(path: &Path) -> NormalizeSnapshot {
    let bytes = fs::read(path).expect("read snapshot");
    serde_json::from_slice(&bytes).expect("parse snapshot")
}

pub fn snapshot_body_digest(path: &Path) -> String {
    let bytes = fs::read(path).expect("read snapshot bytes");
    format!("{:016x}", fnv1a64_bytes(&bytes))
}
