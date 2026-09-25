use crate::model::{AtlasError, Manifest, ManifestSprite, PlacedSprite};
use crate::uv;
use serde::Serialize;
use sha2::{Digest, Sha256};

#[derive(Serialize)]
struct ManifestBody<'a> {
    atlas_width: u32,
    atlas_height: u32,
    padding_px: u32,
    seed: u64,
    sprites: &'a [ManifestSprite],
}

pub fn build_manifest(
    atlas_width: u32,
    atlas_height: u32,
    padding_px: u32,
    seed: u64,
    layout: &[PlacedSprite],
) -> Result<Manifest, AtlasError> {
    let mut sprites: Vec<ManifestSprite> = layout
        .iter()
        .map(|p| {
            let (u0, v0, u1, v1) = uv::uv_rect(
                p.atlas_x,
                p.atlas_y,
                p.content_w,
                p.content_h,
                atlas_width,
                atlas_height,
                padding_px,
            );
            ManifestSprite {
                glyph_id: p.glyph_id.clone(),
                frame: p.frame,
                atlas_x: p.atlas_x,
                atlas_y: p.atlas_y,
                content_w: p.content_w,
                content_h: p.content_h,
                rotate: p.rotate,
                u0,
                v0,
                u1,
                v1,
            }
        })
        .collect();
    sprites.sort_by(|a, b| a.glyph_id.cmp(&b.glyph_id).then(a.frame.cmp(&b.frame)));

    let body = ManifestBody {
        atlas_width,
        atlas_height,
        padding_px,
        seed,
        sprites: &sprites,
    };
    let checksum = checksum_body(&body)?;
    Ok(Manifest {
        atlas_width,
        atlas_height,
        padding_px,
        seed,
        sprites,
        checksum,
    })
}

fn checksum_body(body: &ManifestBody<'_>) -> Result<String, AtlasError> {
    let json = serde_json::to_string_pretty(body).map_err(|e| AtlasError::Parse(e.to_string()))?;
    Ok(hex_sha256(json.as_bytes()))
}

pub fn hex_sha256(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

pub fn write_manifest(path: &std::path::Path, manifest: &Manifest) -> Result<(), AtlasError> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| AtlasError::Io(e.to_string()))?;
    }
    let raw = serde_json::to_string_pretty(manifest).map_err(|e| AtlasError::Parse(e.to_string()))?;
    std::fs::write(path, raw + "\n").map_err(|e| AtlasError::Io(e.to_string()))
}

pub fn read_manifest(path: &std::path::Path) -> Result<Manifest, AtlasError> {
    let raw = std::fs::read_to_string(path).map_err(|e| AtlasError::Io(e.to_string()))?;
    serde_json::from_str(&raw).map_err(|e| AtlasError::Parse(e.to_string()))
}
