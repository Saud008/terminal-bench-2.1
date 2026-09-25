use std::fs;
use std::path::Path;

use crate::resolve::chain::{object_sha1, resolve_all};
use crate::staging;
use crate::types::{ExportObject, PackExport};

pub fn resolve_export(stage_path: &str, export_path: &str) -> Result<(), String> {
    let stage = staging::load_stage(stage_path)?;
    let resolved = resolve_all(&stage)?;

    let mut objects = Vec::new();
    let mut total = 0u64;
    for row in &resolved {
        let inflated_size = row.bytes.len() as u64;
        total += inflated_size;
        objects.push(ExportObject {
            id: apply_id_salt(&row.id),
            kind: row.kind.clone(),
            inflated_size,
            sha1: object_sha1(&row.bytes),
            chain_depth: row.chain_depth,
        });
    }
    objects.sort_by(|a, b| a.id.cmp(&b.id));

    let doc = PackExport {
        pack_id: stage.pack_id,
        objects,
        total_inflated_bytes: total,
    };

    let parent = Path::new(export_path).parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    fs::write(export_path, format!("{pretty}\n")).map_err(|e| e.to_string())
}

fn apply_id_salt(id: &str) -> String {
    if let Ok(salt) = std::env::var("TB3_OBJECT_ID_SALT") {
        if !salt.is_empty() {
            return format!("{id}{salt}");
        }
    }
    id.to_string()
}
