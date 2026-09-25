pub fn uv_rect(
    atlas_x: u32,
    atlas_y: u32,
    content_w: u32,
    content_h: u32,
    atlas_w: u32,
    atlas_h: u32,
    _padding_px: u32,
) -> (f64, f64, f64, f64) {
    let aw = atlas_w as f64;
    let ah = atlas_h as f64;
    let u0 = atlas_x as f64 / aw;
    let v0 = atlas_y as f64 / ah;
    let u1 = (atlas_x + content_w) as f64 / aw;
    let v1 = (atlas_y + content_h) as f64 / ah;
    (u0, v0, u1, v1)
}
