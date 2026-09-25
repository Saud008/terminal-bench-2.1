# Hurtbox active window

Each entity may define a hurtbox with an active frame window and post-spawn invulnerability.

## Fields

| Field | Meaning |
|-------|---------|
| `active_start_frame` | First animation frame the hurtbox may register hits |
| `active_end_frame` | Last animation frame (inclusive) the hurtbox is active |
| `invuln_frames` | Additional frames after `active_start_frame` where hits are ignored |

## Active test

Given animation frame `f` from `frame-index.md`:

```
effective_start = active_start_frame + invuln_frames
active = effective_start <= f <= active_end_frame
```

Hits against the hurtbox are suppressed when `active` is false. Invulnerability is applied after the nominal start frame, not before. Entity-specific window values are defined in the fixture entity catalogs.
