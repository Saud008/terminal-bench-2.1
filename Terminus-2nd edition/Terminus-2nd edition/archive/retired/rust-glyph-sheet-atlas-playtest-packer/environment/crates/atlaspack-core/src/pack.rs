use crate::model::{AtlasError, PlacedSprite, PreparedSprite};

pub fn layout_sprites(
    sprites: &[PreparedSprite],
    atlas_w: u32,
    atlas_h: u32,
) -> Result<Vec<PlacedSprite>, AtlasError> {
    let mut cursor_x = 0u32;
    let mut cursor_y = 0u32;
    let mut row_h = 0u32;
    let mut placed = Vec::with_capacity(sprites.len());

    for sprite in sprites {
        let slot_w = sprite.padded_w;
        let slot_h = sprite.padded_h;

        if cursor_x + slot_w > atlas_w {
            cursor_x = 0;
            cursor_y += row_h;
            row_h = 0;
        }
        if cursor_y + slot_h > atlas_h {
            return Err(AtlasError::Layout("atlas overflow".into()));
        }

        let (content_w, content_h) = (sprite.content_w, sprite.content_h);
        placed.push(PlacedSprite {
            glyph_id: sprite.glyph_id.clone(),
            frame: sprite.frame,
            atlas_x: cursor_x,
            atlas_y: cursor_y,
            content_w,
            content_h,
            rotate: sprite.rotate,
        });

        cursor_x += slot_w;
        row_h = row_h.max(slot_h);
    }
    Ok(placed)
}
