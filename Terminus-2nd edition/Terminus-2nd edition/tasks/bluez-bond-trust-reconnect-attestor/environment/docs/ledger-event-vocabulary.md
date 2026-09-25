# Ledger Event Vocabulary

`ledger_rows` entries always carry an `event` field. The full set of event
names absorb may emit:

| `event` | Emitted by | Notes |
|---------|-----------|-------|
| `seed_bond` | `seed_bond` operation | Registers a bonded device record. |
| `pairing_confirm` | `pairing_confirm` operation | Marks a device pairing-confirmed. |
| `connect` | `connect` operation (allowed) | Reconnect accepted. |
| `connect_rejected` | `connect` operation (rejected) | Carries `reason: pairing_required`; see `pairing-addr-type-gate.md`. |
| `disconnect` | `disconnect` operation | Carries `reason` and `adapter_power`; see `disconnect-power-capture.md`. |
| `bond_remove` | `bond_remove` operation | See `resume-token-revoke.md`. |
| `adapter_power` | `adapter_power` operation | Carries `state`. |
| `gatt_discover` | `gatt_discover` operation | Carries lower-cased `uuid`; see `gatt-uuid-identity.md`. |
| `reconnect_attempt` | `battery_level` operation (accepted) | See `battery-debounce-policy.md`. |
| `reconnect_suppressed` | `battery_level` operation (debounced) | See `battery-debounce-policy.md`. |

The only defined `connect_rejected` reason is `pairing_required`. The
`disconnect` operation's default `reason` when the trace omits one is
`unknown`.

## Module layout

The absorb pipeline lives at `/app/lib/intake/pipeline.sh` (with sibling
`trace_loader.sh` and `device_table.sh`). Policy gates live under
`/app/lib/trustgate/` (`pairing_gate.sh`, `resume_clear.sh`,
`disconnect_capture.sh`, `gatt_identity.sh`, `battery_debounce.sh`). Sealing
lives at `/app/lib/finish/bundle_emit.sh`. This layout is visible directly
under `/app/lib/` and is not required reading to pass any individual test —
it is listed here only so file names referenced elsewhere in the docs and
verifier resolve unambiguously.

## Custom output paths

`--midstate` and `--bundle` accept any writable path, independent of the
documented defaults. For example, absorb with `--midstate
/app/state/alt-midstate.json`, followed by seal with `--midstate
/app/state/alt-midstate.json --bundle /app/output/alt-bundle.json`, produces
`alt-midstate.json` and `alt-bundle.json` without touching the default
midstate or bundle files.

## Hidden trap traces

`/tests/hidden_traces` may contain additional traces exercised only by the
verifier, such as `e2a6e9a7_trap-bond-resume.trace.jsonl`. These exercise
the same policy areas as the bundled fixtures against whichever module
slice is currently installed.
