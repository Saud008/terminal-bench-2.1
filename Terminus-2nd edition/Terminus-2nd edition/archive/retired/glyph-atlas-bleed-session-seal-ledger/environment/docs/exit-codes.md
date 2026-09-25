# Exit codes

Ops exit obligations for the host-local glyph atlas bleed session control plane.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General runtime or I/O error |
| 2 | Oversized sprite after seed scaling exceeds `max_sprite_px` |

`probe` uses code 1 for missing glyph/frame or invalid arguments; it never returns 2.
