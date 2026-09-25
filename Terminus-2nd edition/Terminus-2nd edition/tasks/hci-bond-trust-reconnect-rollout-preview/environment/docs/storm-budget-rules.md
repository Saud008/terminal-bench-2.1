# Reconnect-storm budget contract

Each device lists `battery_probes_ms`, the millisecond timestamps of low-energy battery probe events observed for that device, used as a proxy for reconnect attempts. `/app/config/hciroll.json` declares `debounce_ms` (default `500`) and `max_reconnects_per_window` (default `3`).

## Counting reconnect_attempts

Sort `battery_probes_ms` ascending. The first probe always counts as attempt `1`. Walk the remaining probes in order; a probe counts as a new attempt only when its timestamp is at least `debounce_ms` after the timestamp of the most recently counted attempt (not the previous raw probe). Probes inside the debounce window from the last counted attempt are folded into that attempt and do not increment the count.

For example, with `debounce_ms = 500` and probes `[0, 100, 800]`: `0` counts (attempt 1), `100` is within 500ms of `0` and is folded in, `800` is 800ms after the last counted attempt (`0`) and counts (attempt 2). `reconnect_attempts` is `2`, not `3`.

## Blocking

A device is blocked with reason `ineligible_reconnect_storm` only when its `reconnect_attempts` (computed as above) is strictly greater than `max_reconnects_per_window`. `reconnect_attempts` equal to the budget is not blocked.

`reconnect_attempts` is carried into the reconnect ledger and rollout atlas as a descriptive field on every eligible device row.
