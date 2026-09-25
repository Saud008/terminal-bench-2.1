pub mod atlas;
pub mod catalog;
pub mod decoy;
pub mod export;
pub mod manifest;
pub mod model;
pub mod pack;
pub mod png_io;
pub mod seed;
pub mod staging;
pub mod uv;
pub mod validate;

use std::path::{Path, PathBuf};

pub use model::{AtlasError, Manifest, ProbeResult};

pub fn run_pack(
    catalog_path: &Path,
    sprites_dir: &Path,
    set_name: &str,
    seed: u64,
    atlas_out: &Path,
    manifest_out: &Path,
) -> Result<(), AtlasError> {
    let catalog = catalog::load_catalog(catalog_path)?;
    let entries = catalog::load_pack_entries(&catalog, set_name);
    let padding_px = seed::padding_px(&catalog, seed);
    let prepared = catalog::prepare_sprites(&catalog, &entries, sprites_dir, seed, padding_px)?;
    validate::ensure_fits(&catalog, &prepared)?;
    let layout = pack::layout_sprites(&prepared, catalog.atlas_width, catalog.atlas_height)?;
    let rgba = atlas::compose_atlas(
        &layout,
        &prepared,
        padding_px,
        catalog.atlas_width,
        catalog.atlas_height,
    )?;
    png_io::write_png(atlas_out, catalog.atlas_width, catalog.atlas_height, &rgba)?;
    let manifest = manifest::build_manifest(
        catalog.atlas_width,
        catalog.atlas_height,
        padding_px,
        seed,
        &layout,
    )?;
    manifest::write_manifest(manifest_out, &manifest)?;
    Ok(())
}

pub fn run_probe(
    atlas_path: &Path,
    manifest_path: &Path,
    glyph_id: &str,
    frame: u32,
    u: f64,
    v: f64,
) -> Result<ProbeResult, AtlasError> {
    let manifest = manifest::read_manifest(manifest_path)?;
    let entry = manifest
        .sprites
        .iter()
        .find(|s| s.glyph_id == glyph_id && s.frame == frame)
        .ok_or_else(|| AtlasError::NotFound(format!("{glyph_id}:{frame}")))?;
    let rgba = png_io::read_png(atlas_path)?;
    let (aw, ah) = (manifest.atlas_width, manifest.atlas_height);
    let color = atlas::sample_bilinear(&rgba, aw, ah, entry.u0, entry.v0, entry.u1, entry.v1, u, v);
    Ok(ProbeResult {
        glyph_id: glyph_id.to_string(),
        frame,
        u,
        v,
        rgba: color,
    })
}

pub fn pack_set_names(catalog_path: &Path) -> Result<Vec<String>, AtlasError> {
    let catalog = catalog::load_catalog(catalog_path)?;
    Ok(catalog.pack_sets.iter().map(|s| s.name.clone()).collect())
}

pub fn catalog_path_default() -> PathBuf {
    PathBuf::from("/app/fixtures/catalog.json")
}
