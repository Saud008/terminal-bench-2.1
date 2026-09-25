# Trace Catalog

Bundled trace fixtures live under `/app/fixtures/traces/` and are listed in
`/app/fixtures/catalog.json`. Each fixture exercises one policy area:

| Trace | Role |
|-------|------|
| `pairing-mismatch.trace.jsonl` | Trusted device with `random` bonded address type reconnects with `public` address type before and after a `pairing_confirm`; exercises the pairing/address-type gate. |
| `bond-remove-resume.trace.jsonl` | Bonded device with a resume token is removed via `bond_remove`, then reconnects; exercises resume-token clearing. |
| `power-disconnect-order.trace.jsonl` | A `disconnect` is immediately followed by an `adapter_power` state change; exercises disconnect power-capture seq-capture. |
| `gatt-uuid-dedupe.trace.jsonl` | The same GATT UUID is rediscovered with different letter case alongside one distinct UUID; exercises GATT identity dedupe. |
| `battery-reconnect-storm.trace.jsonl` | Three `battery_level` probes for one device, two within the debounce window and one outside it; exercises reconnect debouncing. |
| `mixed-fleet-core.trace.jsonl` | One device exercising seed, pairing confirm, connect, GATT discovery, disconnect, adapter power cycling, and bond removal in a single run; used for full absorb+seal pipeline checks. |

`TB3_TRACE_DIR`, when set to an absolute path, causes a relative `--trace`
argument to resolve against that directory instead of
`/app/fixtures/traces/`. The verifier uses this to exercise additional
traces that are not enumerated here.

Verifier seeds are opaque strings recorded verbatim into both the midstate
snapshot and the attestation bundle. Example seeds used in contract checks
include `seed-carry-through`, `seed-full-pipeline`, `seed-default-midstate`,
`seed-default-bundle`, `seed-fingerprint`, `seed-ingest-only`,
`seed-ledger-order`, `seed-partial-battery`, and `seed-partial-pairing`.
