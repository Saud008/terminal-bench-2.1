# Battery-Driven Reconnect Debounce

`battery_level` operations are treated as reconnect probes. Each carries a
`ts` and a `mac`. The absorb config (`/app/config/bondattest.json`, field
`debounce_ms`) defines the debounce window per device.

For each device, track the `ts` of its last accepted reconnect attempt
(initialized as if the last attempt were far in the past). When a
`battery_level` operation arrives for that device:

- If `ts - last_ts < debounce_ms`, the reconnect is suppressed: a
  `reconnect_suppressed` ledger row is written and `reconnect_attempts` is
  **not** incremented.
- Otherwise, the reconnect is accepted: `last_ts` is updated to the new
  `ts`, a `reconnect_attempt` ledger row is written, and
  `reconnect_attempts` is incremented by one.

Debounce state is tracked independently per `mac`.
