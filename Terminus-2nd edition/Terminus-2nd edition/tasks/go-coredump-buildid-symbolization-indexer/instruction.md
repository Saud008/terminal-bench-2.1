Forensic crash-evidence authenticity operators need a host-local GNU build-ID attestation control plane at `/app/bin/coreidx`. The plane admits offline crash-bundle directories, enforces companion-ELF build-ID authenticity and half-open mmap integrity trust gates, applies catalog policy only when stripped mappings lack a trusted note, groups duplicate evidence under a chain-of-custody key, and publishes digest-bound sealed attestations from on-disk staging only. This is a security authenticity and chain-of-custody attestation workflow; keep build-ID authenticity admission, mmap integrity gates, catalog trust fallback, tamper-evident staging, and sealed SQLite/summary export aligned. It is not a debugging, symbolization-indexer, or generic CLI-engineering exercise.

Task identity `1066c154bf` and the integrity failure envelope are in `/app/docs/integrity-admission-contract.md`.

## Artifacts

- `/app/state/crash_staging.jsonl` — tamper-evident staging after admitted ingest (alternate writable JSONL such as `/app/state/alt_staging.jsonl` is allowed)
- `/app/output/crash_index.sqlite` — sealed SQLite attestation with `crash_groups` and `crash_frames`
- `/app/output/crash_summary.json` — sealed summary bound to staging groups and `totals.group_count`

## Integrity contracts

Contracts require uppercase hex `build_id` values without prefixes, mmap hits on half-open intervals, authentic symbol names for admitted frames, `group_key` ordering in export groups, and `totals.group_count` matching the groups table length. Operator surfaces and layout follow `/app/docs/cli_surface.md`, `/app/docs/crash_bundle_format.md`, `/app/docs/elf_buildid_notes.md`, `/app/docs/mmap_range_matching.md`, `/app/docs/stripped_fallback.md`, `/app/docs/dedupe_grouping.md`, `/app/docs/staging_pipeline.md`, and `/app/docs/sqlite_export_schema.md`.

## Subcommands

```text
coreidx ingest --crash-dir DIR --catalog PATH --staging PATH
coreidx export --staging PATH --sqlite PATH --summary PATH
```

## Constraints

`coreidx ingest` must persist staging under the caller-provided `--staging` path. `coreidx export` may publish sealed SQLite and summary outputs only from that staging path. Static fixture copies cannot satisfy grading. Release binary path is `/app/bin/coreidx` per `/app/docs/staging_pipeline.md`. When `TB3_CRASH_DIR` is set, ingest must read `.crash.jsonl` files from that directory. Bundled fixtures live under `/app/fixtures`. Do not edit `/app/docs/` or `/app/fixtures/`.
