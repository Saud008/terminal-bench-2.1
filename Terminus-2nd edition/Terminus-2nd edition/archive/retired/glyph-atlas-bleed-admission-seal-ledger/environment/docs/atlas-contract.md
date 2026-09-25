# Atlas pad-bleed admission contract

Normative pad-bleed and UV admission gates for the host-local glyph atlas bleed admission control plane.

## Padding and bleed

Each admitted sprite is allocated a padded rectangle in the sealed atlas. Let `padding_px` come from the catalog seed policy (see manifest schema).

- Padded size: `(content_w + 2 * padding_px, content_h + 2 * padding_px)`.
- PNG pixels are copied into the inner content slot at offset `(padding_px, padding_px)`.
- The one-pixel border around the content is filled by **replicating** the nearest content edge pixel (clamp sampling from the content, not transparent fill).

## UV rectangles

Sealed manifest UV values are normalized floats in `[0, 1]` relative to the final atlas dimensions.

They describe the **inner drawable content**, not the padded gutter:

- `u0 = (atlas_x + padding_px) / atlas_width`
- `v0 = (atlas_y + padding_px) / atlas_height`
- `u1 = (atlas_x + padding_px + content_w) / atlas_width`
- `v1 = (atlas_y + padding_px + content_h) / atlas_height`

Bilinear sampling at `(u0, v0)` or `(u1, v1)` must return the sprite edge color, not a neighbor tile.

## Rotation

When `rotate` is true on a catalog entry, admission places the sprite using **swapped** content width and height for shelf allocation. The PNG is rotated 90° clockwise when composited. UV dimensions reflect the post-rotation content size.

## Duplicate glyph frames

Catalog entries are uniquely identified by `(glyph_id, frame)`. Multiple frames under the same glyph id must all appear in the sealed manifest.

## Seed scaling

Entries listed in catalog `scalable` multiply both content dimensions by `1 + (seed % scale_mod)` before packing. Dimensions are rounded up to at least 1 pixel.

## Size limit

If any sprite after scaling would require `padded_w > max_sprite_px` or `padded_h > max_sprite_px`, admission aborts before writing sealed outputs.
