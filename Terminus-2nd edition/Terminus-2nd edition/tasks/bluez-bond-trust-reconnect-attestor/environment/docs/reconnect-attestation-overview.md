# Reconnect Attestation Overview

`bondattest` turns a synthetic BlueZ D-Bus bonding trace into a sealed reconnect
attestation bundle in two steps:

1. **absorb** — absorbs a trace's operations in `seq`/`ts` order against the
   reconnect trust policy, accumulates a reconnect ledger, and writes a
   midstate snapshot to `/app/state/bondattest-midstate.json` (default).
2. **seal** — reads the midstate snapshot, folds the ledger into a
   `ledger_fingerprint`, and writes the final attestation bundle to
   `/app/output/bond-reconnect-attestation.json` (default) with a
   `bundle_seal` that binds the midstate digest, ledger fingerprint, and run
   seed together.

The two steps are independent CLI invocations so a midstate snapshot can be
inspected, archived, or resealed without re-absorbing the trace.

## Trace operations

Every trace row carries `seq`, `ts`, and `op`. Rows are sorted by
`(seq, ts)` before absorb. The supported operations are:

| op | Fields | Effect |
|----|--------|--------|
| `seed_bond` | `mac`, `addr_type`, `trusted`, `resume_token` | Registers a bonded device record. |
| `pairing_confirm` | `mac` | Marks the device as freshly pairing-confirmed. |
| `connect` | `mac`, `addr_type` | Attempts a reconnect; see `pairing-addr-type-gate.md`. |
| `disconnect` | `mac`, `reason` | Records a disconnect reason; see `disconnect-power-capture.md`. |
| `bond_remove` | `mac` | Clears the bond; see `resume-token-revoke.md`. |
| `adapter_power` | `state` (`on`/`off`) | Updates adapter power state. |
| `gatt_discover` | `mac`, `uuid` | Records a GATT characteristic discovery; see `gatt-uuid-identity.md`. |
| `battery_level` | `mac`, `level`, `ts` | Drives reconnect debouncing; see `battery-debounce-policy.md`. |

See `cli.md` for the exact command-line contract, `trace-catalog.md` for the
bundled fixture roles, and `midstate-and-bundle-seals.md` for the digest
formulas used to seal each artifact.
