# Sheet gutter-edge admission contract

Normative gutter-edge and sample-window admission gates for the host-local labelsheet imposition admission control plane.

## Gutter and edge replication

Each admitted mark is allocated a guttered rectangle on the sealed sheet. Let `gutter_px` come from the catalog seed policy (see ledger schema).

- Guttered size: `(content_w + 2 * gutter_px, content_h + 2 * gutter_px)`.
- PNG pixels are copied into the inner content slot at offset `(gutter_px, gutter_px)`.
- The one-pixel border around the content is filled by **replicating** the nearest content edge pixel (clamp sampling from the content, not transparent fill).

## Normalized sample windows

Sealed ledger sample-window values are normalized floats in `[0, 1]` relative to the final sheet dimensions.

They describe the **inner printable content**, not the gutter:

- `u0 = (sheet_x + gutter_px) / sheet_width`
- `v0 = (sheet_y + gutter_px) / sheet_height`
- `u1 = (sheet_x + gutter_px + content_w) / sheet_width`
- `v1 = (sheet_y + gutter_px + content_h) / sheet_height`

Sampling at `(u0, v0)` or `(u1, v1)` must return the mark edge color, not a neighbor cell.

## Press-rotate

When `press_rotate` is true on a catalog entry, admission places the mark using **swapped** content width and height for shelf allocation. The PNG is rotated 90° clockwise when composited. Sample-window dimensions reflect the post-rotation content size.

## Duplicate mark frames

Catalog entries are uniquely identified by `(mark_id, frame)`. Multiple frames under the same mark id must all appear in the sealed ledger.

## Lot-scale multipliers

Entries listed in catalog `scalable` multiply both content dimensions by `1 + (seed % scale_mod)` before imposition. Dimensions are rounded up to at least 1 pixel.

## Size limit

If any mark after scaling would require `padded_w > max_mark_px` or `padded_h > max_mark_px`, admission aborts before writing sealed outputs.
