# Bind snapshot artifact (stage 1)

`nlctl decode` is a **multi-stage** pipeline:

| Stage | Module | Output |
|-------|--------|--------|
| 1 Bind | bind.rs | JSON under /app/state/bind-snapshots named dump-filename-pid.json |
| 1b Guard | snapshot_guard.rs | validates bind snapshot (see /app/docs/stage1b-guard.md) |
| 2a Export NH | export_nh.rs | JSON under /app/state/nh-snapshots named dump-filename-pid.json |
| 2b Export | export.rs | caller --output schedule JSON including export_digest |

Stage 1 parses the dump (`decode.rs`) and binds routes (`bind.rs`). Stage 1b validates the bind snapshot (`snapshot_guard.rs`). Stage 2a reads the bind snapshot and normalizes nexthops (`export_nh.rs`) — see `/app/docs/nh-stage-artifact.md`. Stage 2b assembles the export document (`export.rs`) from the NH snapshot only — it **must not** re-read the dump, re-run bind, or re-read the bind snapshot for route assembly.

## Snapshot schema (version 1)

```json
{
  "version": 1,
  "seed": "nl-seed-6",
  "source_dump": "/app/fixtures/dumps/001-multipath-v4.bin",
  "routes": [ ... ]
}
```

| Field | Meaning |
|-------|---------|
| `version` | Always `1` |
| `seed` | UTF-8 seed from the dump header |
| `source_dump` | Absolute `--dump` path passed to `nlctl decode` |
| `routes` | Bound `RouteOut` rows in **dump message order** |

Each `routes[]` entry follows the export row shape from `/app/docs/export-digest-schema.md`, but stage 1 does **not** apply export ordering rules.

Binding algorithms are defined in `/app/docs/nexthop-bind-contract.md` and `/app/docs/nldm-dump-wire.md`. Export ordering is defined in `/app/docs/export-digest-schema.md`.
