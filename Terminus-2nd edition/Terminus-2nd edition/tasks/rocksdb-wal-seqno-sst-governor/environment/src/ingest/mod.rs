use std::fs;
use std::path::Path;

use crate::types::{
    ManifestInput, SstFileInput, SstFileRow, StageFile, WalBatchInput, WalBatchRow,
};

pub fn ingest_fixture_dir(dir: &str, stage_path: &str) -> Result<(), String> {
    let manifest_path = Path::new(dir).join("manifest.json");
    let raw = fs::read_to_string(&manifest_path).map_err(|e| e.to_string())?;
    let manifest: ManifestInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

    let wal_batches = load_wal_dir(&Path::new(dir).join("wal"))?;
    let sst_files = load_sst_dir(&Path::new(dir).join("sst"))?;

    let prev_seq = crate::staging::load_stage(stage_path)
        .ok()
        .map(|s| s.ingest_seq)
        .unwrap_or(0);

    let stage = StageFile {
        ingest_seq: prev_seq + 1,
        snapshot_seqno: manifest.snapshot_seqno,
        watermark_seqno: manifest.watermark_seqno,
        wal_batches,
        sst_files,
    };
    crate::staging::save_stage(stage_path, &stage)
}

fn load_wal_dir(wal_dir: &Path) -> Result<Vec<WalBatchRow>, String> {
    let names = list_json(wal_dir)?;
    let mut rows = Vec::new();
    for (idx, name) in names.iter().enumerate() {
        let path = wal_dir.join(name);
        let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let input: WalBatchInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        rows.push(WalBatchRow {
            batch_id: input.batch_id,
            seqno: input.seqno,
            committed: input.committed,
            cf: input.cf,
            puts: input.puts,
            point_tombstones: input.point_tombstones,
            source: name.clone(),
            ingest_order: (idx + 1) as u32,
        });
    }
    Ok(rows)
}

fn load_sst_dir(sst_dir: &Path) -> Result<Vec<SstFileRow>, String> {
    let names = list_json(sst_dir)?;
    let mut rows = Vec::new();
    for (idx, name) in names.iter().enumerate() {
        let path = sst_dir.join(name);
        let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let input: SstFileInput = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        rows.push(SstFileRow {
            file_id: input.file_id,
            cf: input.cf,
            level: input.level,
            size_bytes: input.size_bytes,
            min_seqno: input.min_seqno,
            max_seqno: input.max_seqno,
            keys: input.keys,
            point_tombstones: input.point_tombstones,
            range_tombstones: input.range_tombstones,
            merge_operands: input.merge_operands,
            source: name.clone(),
            ingest_order: (idx + 1) as u32,
        });
    }
    Ok(rows)
}

fn list_json(dir: &Path) -> Result<Vec<String>, String> {
    let entries = fs::read_dir(dir).map_err(|e| e.to_string())?;
    let mut names: Vec<String> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .filter(|n| n.ends_with(".json"))
        .collect();
    names.sort();
    Ok(names)
}
