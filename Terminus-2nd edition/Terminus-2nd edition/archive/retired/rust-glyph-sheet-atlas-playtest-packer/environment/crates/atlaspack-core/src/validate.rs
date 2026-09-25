use crate::model::{AtlasError, Catalog, PreparedSprite};

pub fn ensure_fits(catalog: &Catalog, sprites: &[PreparedSprite]) -> Result<(), AtlasError> {
    for sprite in sprites {
        if sprite.padded_w > catalog.max_sprite_px || sprite.padded_h > catalog.max_sprite_px {
            return Err(AtlasError::Oversized(format!(
                "{}:{} exceeds max {}",
                sprite.glyph_id, sprite.frame, catalog.max_sprite_px
            )));
        }
    }
    Ok(())
}
