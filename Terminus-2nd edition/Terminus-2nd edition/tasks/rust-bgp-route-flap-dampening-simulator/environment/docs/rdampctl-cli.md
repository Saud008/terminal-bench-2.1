# rdampctl CLI

Binary: /app/bin/rdampctl

Release layout (verifier rebuild): `/usr/local/cargo/bin/cargo` builds the crate under `/app` and places the binary at `/app/target/release/rdampctl` for install into `/app/bin/rdampctl`.

## compile-scenario

```
rdampctl compile-scenario --scenario SCENARIO [--root DIR]
```

Writes /app/state/scenario-lock.json on success.

## drive-feed

```
rdampctl drive-feed --scenario SCENARIO [--root DIR]
```

Requires lock for scenario_id. Re-reads feed from disk, writes /app/state/flap-ledger.json, advances run_id.

## emit-atlas

```
rdampctl emit-atlas --scenario SCENARIO --out PATH [--root DIR]
```

Requires run_id greater than zero. Writes JSONL per flap-suppression-jsonl.md.

## emit-reuse-forecast

```
rdampctl emit-reuse-forecast --scenario SCENARIO --out PATH [--root DIR]
```

Requires run_id greater than zero and a flap ledger. Writes JSONL per reuse-timer-forecast.md.

Default root: /app/fixtures

Environment:
- TB3_FIXTURE_DIR overrides root
- TB3_HALF_LIFE_BIAS adds to each peer half_life_ms at compile-scenario
