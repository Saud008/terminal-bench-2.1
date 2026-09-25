# relationwatchd

Host-local revision-watch ops control plane (admit → gate → sealed membership report).

## Layout

- cmd/relationwatchd — operator entrypoint (`serve`)
- internal/ — admission, gate, snapshot, and sealed-export policy packages
- docs/ — ops contracts referenced by the instruction
- fixtures/ — seed bundles for the seed ops verb
- config/relationwatch.json — runtime paths and stale-lag threshold
- scripts/verifier-rebuild.sh — evaluation rebuild from sources under /app

## Build

```bash
export CGO_ENABLED=0
go build -mod=readonly -o relationwatchd ./cmd/relationwatchd
./relationwatchd serve --config /app/config/relationwatch.json
```

## Ops verbs

Seed, tuple write, membership check, filtered revision watch, sealed export, and namespace-prefix delete. Request bodies and field contracts are defined under /app/docs/.
