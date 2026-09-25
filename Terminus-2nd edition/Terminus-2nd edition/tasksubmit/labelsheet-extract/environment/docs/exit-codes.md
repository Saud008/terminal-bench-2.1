# Exit codes

Ops exit obligations for the host-local labelsheet imposition admission control plane.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General runtime or I/O error |
| 2 | Oversized mark after lot-scale exceeds `max_mark_px` |

`sample` uses code 1 for missing mark/frame or invalid arguments; it never returns 2.
