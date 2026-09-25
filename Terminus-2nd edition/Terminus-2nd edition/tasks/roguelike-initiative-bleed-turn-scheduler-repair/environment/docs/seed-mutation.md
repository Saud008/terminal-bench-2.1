# Seed mutation

Given non-empty seed string:

```
idx = fnv1a64(seed) % actor_count
delta = 1 + (fnv1a64(seed + ":bleed") % 3)
actors[idx].bleed += delta
```

Applied once before round 1. FNV-1a64 uses offset basis `0xcbf29ce484222325` and prime `0x100000001b3`.

Seeds listed in `/app/fixtures/seeds.json`.
