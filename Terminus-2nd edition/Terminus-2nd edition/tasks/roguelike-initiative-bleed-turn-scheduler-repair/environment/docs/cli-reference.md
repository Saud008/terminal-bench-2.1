# CLI reference

Binary: `/usr/local/bin/turnctl` (build with `cargo build --locked --release --bin turnctl` from `/app`, then `install -m 0755 target/release/turnctl /usr/local/bin/turnctl`).

## ingest

```
turnctl ingest --roster /app/fixtures/rosters/<name>.json --staging /app/output/<name>.staging.json
```

Validates roster JSON, writes staging document with checksum. Exits `1` on invalid roster (empty actors, non-positive hp, negative bleed).

## simulate

```
turnctl simulate \
  --staging /app/output/<name>.staging.json \
  --seed <seed> \
  --state /app/output/<name>-<seed>.state.json \
  --export /app/output/<name>-<seed>.json
```

Runs combat for `rounds` from staging, applies per-seed bleed mutation, writes persistence state and transcript export.

## export

```
turnctl export --state /app/output/<name>-<seed>.state.json --export /app/output/<name>-<seed>.reexport.json
```

Re-exports transcript from persisted state without re-simulating.

Output directory: `/app/output/` (reset with `/app/scripts/reset-state.sh`).
