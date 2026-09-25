use crate::slot_math::slot_count;
use crate::manifest_read::ArrayManifest;
use std::collections::BTreeSet;

pub fn enumerate_chunk_keys(manifest: &ArrayManifest) -> Vec<String> {
    if manifest.shape.len() < 2 || manifest.chunks.len() < 2 {
        return Vec::new();
    }
    let ni = (manifest.shape[0] + manifest.chunks[0] - 1) / manifest.chunks[0];
    let nj = (manifest.shape[1] + manifest.chunks[1] - 1) / manifest.chunks[1];
    let mut keys = Vec::new();
    for i in 0..ni {
        for j in 0..nj {
            keys.push(format!("{i}.{j}"));
        }
    }
    keys
}

pub fn absent_chunk_keys(manifest: &ArrayManifest) -> Vec<String> {
    let expected: BTreeSet<String> = enumerate_chunk_keys(manifest).into_iter().collect();
    let present: BTreeSet<String> = manifest.chunk_keys.iter().cloned().collect();
    let mut missing = Vec::new();
    for key in &manifest.chunk_keys {
        if expected.contains(key) {
            missing.push(key.clone());
        }
    }
    for key in expected.difference(&present) {
        missing.push(key.clone());
    }
    missing.sort();
    missing.dedup();
    missing
}

pub fn present_count(manifest: &ArrayManifest) -> u64 {
    manifest.chunk_keys.len() as u64
}

pub fn expected_count(manifest: &ArrayManifest) -> u64 {
    slot_count(manifest)
}
