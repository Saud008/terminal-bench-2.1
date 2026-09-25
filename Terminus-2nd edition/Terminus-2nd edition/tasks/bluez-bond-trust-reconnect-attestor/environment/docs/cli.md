# bondattest CLI

The entrypoint script lives at `/app/scripts/bondattest` and is installed to
`/usr/local/bin/bondattest`.

```
bondattest absorb --trace PATH --config PATH --seed SEED [--midstate PATH]
bondattest seal [--midstate PATH] [--bundle PATH]
```

- `--trace` may be an absolute path, or a bare filename. A bare filename
  resolves under `TB3_TRACE_DIR` (if set to an absolute path), otherwise
  under `/app/fixtures/traces/`.
- `--config` points at a JSON file with a `debounce_ms` integer field (see
  `/app/config/bondattest.json`).
- `--seed` is an opaque string carried through into the midstate snapshot and
  the final bundle; it also participates in the `bundle_seal` formula.
Default output paths (also stated in the task instruction):

- `/app/state/bondattest-midstate.json`
- `/app/output/bond-reconnect-attestation.json`

- `--midstate` defaults to `/app/state/bondattest-midstate.json` when omitted.
- `--bundle` defaults to `/app/output/bond-reconnect-attestation.json` when
  omitted.

`seal` only reads the midstate snapshot produced by a prior `absorb`; it does
not re-read the original trace.

Run `/app/scripts/reset-state.sh` between independent verifier runs to clear
prior midstate/bundle output and run-scoped state.

The helper under `/app/lib/decoy/` is not sourced by either the `absorb` or
`seal` code paths and must not appear in the emitted midstate or bundle JSON.
