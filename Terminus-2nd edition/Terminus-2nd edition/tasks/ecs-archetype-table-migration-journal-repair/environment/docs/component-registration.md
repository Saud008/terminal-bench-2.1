# Component registration order

`component_names` in a world spec lists declared components. The `--seed` string assigns stable numeric ids before any entity load or journal replay.

## Algorithm

1. Start with `order` = `component_names` in file order (do not sort).
2. `state = u64::from_le_bytes(SHA256(seed.as_bytes())[0..8])`.
3. Fisher–Yates shuffle from the last index down to 1:
   - `state = xorshift64(state)` where `xorshift64` is:
     - `x ^= x << 13`
     - `x ^= x >> 7`
     - `x ^= x << 17`
     - all on `u64` with wrap
   - `j = (state as usize) % (i + 1)`
   - swap `order[i]` and `order[j]`
4. `component_map[name] = index in final order` (0-based).

The same seed and name list must always produce the same map. Journal ops resolve component names through this map.
