//! Layout manifest ingest and parse helpers for ecs-migrate apply.
use crate::model::LayoutManifest;
use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

pub fn load_layout(path: &Path) -> Result<LayoutManifest> {
    let raw = fs::read_to_string(path).with_context(|| format!("read layout {}", path.display()))?;
    let manifest: LayoutManifest = serde_json::from_str(&raw).context("parse layout json")?;
    Ok(manifest)
}

pub fn component_stride(manifest: &LayoutManifest) -> u32 {
    manifest
        .components
        .iter()
        .map(|c| c.offset + c.size)
        .max()
        .unwrap_or(0)
}

pub fn signature_for_payload(manifest: &LayoutManifest, payload: &[u8]) -> String {
    let stride = component_stride(manifest) as usize;
    let mut names: Vec<String> = Vec::new();
    for comp in &manifest.components {
        let start = comp.offset as usize;
        let end = start + comp.size as usize;
        if end <= stride && end <= payload.len() {
            let slice = &payload[start..end];
            if slice.iter().any(|b| *b != 0) {
                names.push(comp.name.clone());
            }
        }
    }
    names.sort();
    names.join("+")
}
