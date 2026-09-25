use crate::model::{AtlasError, PlacedSprite, PreparedSprite};
use std::collections::HashMap;

pub fn compose_atlas(
    layout: &[PlacedSprite],
    prepared: &[PreparedSprite],
    padding_px: u32,
    atlas_w: u32,
    atlas_h: u32,
) -> Result<Vec<u8>, AtlasError> {
    let mut rgba = vec![0u8; (atlas_w * atlas_h * 4) as usize];
    let lookup: HashMap<(String, u32), &PreparedSprite> = prepared
        .iter()
        .map(|p| ((p.glyph_id.clone(), p.frame), p))
        .collect();

    for place in layout {
        let sprite = lookup
            .get(&(place.glyph_id.clone(), place.frame))
            .ok_or_else(|| AtlasError::Layout("missing prepared sprite".into()))?;
        blit_sprite(
            &mut rgba,
            atlas_w,
            atlas_h,
            place.atlas_x,
            place.atlas_y,
            padding_px,
            sprite.content_w,
            sprite.content_h,
            &sprite.pixels,
        );
    }
    Ok(rgba)
}

fn blit_sprite(
    atlas: &mut [u8],
    atlas_w: u32,
    _atlas_h: u32,
    atlas_x: u32,
    atlas_y: u32,
    padding_px: u32,
    content_w: u32,
    content_h: u32,
    src: &[u8],
) {
    for y in 0..content_h {
        for x in 0..content_w {
            let si = ((y * content_w + x) * 4) as usize;
            let dx = atlas_x + padding_px + x;
            let dy = atlas_y + padding_px + y;
            put_pixel(atlas, atlas_w, dx, dy, &src[si..si + 4]);
        }
    }
}

fn put_pixel(buf: &mut [u8], width: u32, x: u32, y: u32, rgba: &[u8]) {
    let idx = ((y * width + x) * 4) as usize;
    buf[idx..idx + 4].copy_from_slice(rgba);
}

pub fn sample_bilinear(
    rgba: &[u8],
    atlas_w: u32,
    atlas_h: u32,
    u0: f64,
    v0: f64,
    u1: f64,
    v1: f64,
    u: f64,
    v: f64,
) -> [u8; 4] {
    let px = u0 + u * (u1 - u0);
    let py = v0 + v * (v1 - v0);
    let fx = px * atlas_w as f64 - 0.5;
    let fy = py * atlas_h as f64 - 0.5;
    let x0 = fx.floor().max(0.0) as u32;
    let y0 = fy.floor().max(0.0) as u32;
    let x1 = (x0 + 1).min(atlas_w.saturating_sub(1));
    let y1 = (y0 + 1).min(atlas_h.saturating_sub(1));
    let tx = fx - fx.floor();
    let ty = fy - fy.floor();

    let c00 = sample_nearest(rgba, atlas_w, x0, y0);
    let c10 = sample_nearest(rgba, atlas_w, x1, y0);
    let c01 = sample_nearest(rgba, atlas_w, x0, y1);
    let c11 = sample_nearest(rgba, atlas_w, x1, y1);
    lerp4(c00, c10, c01, c11, tx, ty)
}

fn sample_nearest(rgba: &[u8], width: u32, x: u32, y: u32) -> [u8; 4] {
    let idx = ((y * width + x) * 4) as usize;
    let mut out = [0u8; 4];
    out.copy_from_slice(&rgba[idx..idx + 4]);
    out
}

fn lerp4(a: [u8; 4], b: [u8; 4], c: [u8; 4], d: [u8; 4], tx: f64, ty: f64) -> [u8; 4] {
    let mut out = [0u8; 4];
    for i in 0..4 {
        let top = a[i] as f64 + (b[i] as f64 - a[i] as f64) * tx;
        let bot = c[i] as f64 + (d[i] as f64 - c[i] as f64) * tx;
        out[i] = (top + (bot - top) * ty).round() as u8;
    }
    out
}
