use std::fs;
use std::path::Path;

use crate::ingest;
use crate::sketch;
use crate::staging;
use crate::types::GenerationFile;
use crate::DEFAULT_GENERATION_PATH;

pub fn run_merge(seed: &str, bundle_id: &str, fixture_root: &str) -> Result<(), String> {
    let mut snap = staging::read_stage()?;
    if snap.bundle_id != bundle_id {
        return Err("staging bundle mismatch".into());
    }
    let shards = ingest::load_shards_for_bundle(seed, bundle_id, fixture_root)?;
    let weights: Vec<f64> = shards
        .iter()
        .map(|s| {
            snap.window_weights
                .get(&s.shard_id)
                .copied()
                .unwrap_or(0.0)
        })
        .collect();
    let mut tables = Vec::new();
    for shard in &shards {
        let updates: Vec<(String, u64)> = shard
            .updates
            .iter()
            .map(|u| (u.key.clone(), u.count))
            .collect();
        tables.push(sketch::build_table(
            shard.width,
            shard.depth,
            shard.hash_seed,
            &shard.namespace_salt,
            &updates,
        ));
    }
    let merged = sketch::merge_tables(&tables, &weights);
    snap.merged_counters = Some(merged);
    let gen = read_generation()?.merge_generation + 1;
    snap.merge_generation = gen;
    staging::write_stage(&snap)?;
    write_generation(gen)
}

fn read_generation() -> Result<GenerationFile, String> {
    let path = Path::new(DEFAULT_GENERATION_PATH);
    if !path.exists() {
        return Ok(GenerationFile {
            merge_generation: 0,
        });
    }
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn write_generation(gen: u64) -> Result<(), String> {
    let path = Path::new(DEFAULT_GENERATION_PATH);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let body = GenerationFile {
        merge_generation: gen,
    };
    fs::write(path, serde_json::to_string_pretty(&body).unwrap()).map_err(|e| e.to_string())
}
