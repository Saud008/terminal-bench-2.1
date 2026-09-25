# UDP input reconciler

`udpctl` replays hex-encoded UDP input frames through ingest, staging, and export.

```bash
udpctl ingest \
  --bundle /app/fixtures/bundles/baseline.json \
  --seed 7

udpctl export \
  --export /app/output/replay-report.json
```

Combined replay:

```bash
udpctl replay \
  --bundle /app/fixtures/bundles/baseline.json \
  --seed 7 \
  --export /app/output/replay-report.json
```

Ingest writes `/app/state/replay-staging.json`. Export reads staging and writes JSON to the exact `--export` path.

Contracts live under `/app/docs/`. Fixture bundles are under `/app/fixtures/bundles/`.

## Container image

The image uses the canonical digest-pinned **`public.ecr.aws/docker/library/rust:1.85-slim`** base (`linux/amd64`). Agents implement the ingest and export pipeline under `/app/crates` and rebuild `udpctl`; the verifier rebuilds before behavioral checks.
