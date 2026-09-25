# Normalize contract

All exports and staging documents use UTF-8 JSON with trailing newline. Pretty-printed staging/state files use two-space indent.

## Staging document

Fields: `staging_version` (1), `rounds`, `actors`, `checksum`.

`checksum` is SHA-256 hex of compact JSON array of actors in roster field order (see `/app/docs/roster-format.md`).

## Transcript export

Fields: `export_version` (1), `seed`, `transcript_hash`, `rounds`, `actors_final`.

`transcript_hash` is SHA-256 hex of compact JSON encoding of the `rounds` array exactly as stored in combat state (event order preserved; no reordering).

`actors_final` lists actors after simulation with death/pin/stun flags cleared per `/app/docs/death-and-pin.md`.

## Persistence state

Fields: `state_version` (1), `seed`, `rounds_planned`, `actors`, `rounds`.

Written by simulate; read by export. Must round-trip without mutation.

## Seed bleed mutation

When `seed` is non-empty, FNV-1a64 selects one actor index and adds `1 + (fnv1a64(seed + ":bleed") % 3)` to that actor's bleed before round 1. Documented in `/app/docs/seed-mutation.md`.
