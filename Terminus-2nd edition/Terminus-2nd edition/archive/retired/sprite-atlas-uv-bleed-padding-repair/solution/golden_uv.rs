pub fn uv_rect(
    atlas_x: u32,
    atlas_y: u32,
    content_w: u32,
    content_h: u32,
    atlas_w: u32,
    atlas_h: u32,
    padding_px: u32,
) -> (f64, f64, f64, f64) {
    let aw = atlas_w as f64;
    let ah = atlas_h as f64;
    let inner_x = atlas_x + padding_px;
    let inner_y = atlas_y + padding_px;
    let u0 = inner_x as f64 / aw;
    let v0 = inner_y as f64 / ah;
    let u1 = (inner_x + content_w) as f64 / aw;
    let v1 = (inner_y + content_h) as f64 / ah;
    (u0, v0, u1, v1)
}
