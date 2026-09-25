use crate::model::{AtlasError, Catalog, PreparedSprite, SpriteRef};
use crate::png_io;
use crate::seed;
use std::collections::HashMap;
use std::path::Path;

pub fn load_catalog(path: &Path) -> Result<Catalog, AtlasError> {
    let raw = std::fs::read_to_string(path).map_err(|e| AtlasError::Io(e.to_string()))?;
    serde_json::from_str(&raw).map_err(|e| AtlasError::Parse(e.to_string()))
}

pub fn load_pack_entries(catalog: &Catalog, set_name: &str) -> Vec<SpriteRef> {
    let set = catalog
        .pack_sets
        .iter()
        .find(|s| s.name == set_name)
        .unwrap_or_else(|| panic!("unknown pack set {set_name}"));
    let mut by_glyph: HashMap<String, SpriteRef> = HashMap::new();
    for sprite in &set.sprites {
        by_glyph.insert(sprite.glyph_id.clone(), sprite.clone());
    }
    by_glyph.into_values().collect()
}

pub fn prepare_sprites(
    catalog: &Catalog,
    entries: &[SpriteRef],
    sprites_dir: &Path,
    seed: u64,
    padding_px: u32,
) -> Result<Vec<PreparedSprite>, AtlasError> {
    let scale = seed::scale_factor(catalog, seed);
    let mut out = Vec::with_capacity(entries.len());
    for entry in entries {
        let path = sprites_dir.join(&entry.file);
        let (mut w, mut h, mut pixels) = png_io::read_png_size(&path)?;
        if catalog.scalable.iter().any(|g| g == &entry.glyph_id) {
            let nw = seed::scaled_dim(w, scale);
            let nh = seed::scaled_dim(h, scale);
            pixels = png_io::resize_nearest(&pixels, w, h, nw, nh);
            w = nw;
            h = nh;
        }
        let (content_w, content_h) = if entry.rotate { (w, h) } else { (w, h) };
        let padded_w = content_w + padding_px * 2;
        let padded_h = content_h + padding_px * 2;
        out.push(PreparedSprite {
            glyph_id: entry.glyph_id.clone(),
            frame: entry.frame,
            rotate: entry.rotate,
            content_w,
            content_h,
            padded_w,
            padded_h,
            pixels,
        });
    }
    out.sort_by(|a, b| a.glyph_id.cmp(&b.glyph_id).then(a.frame.cmp(&b.frame)));
    Ok(out)
}
