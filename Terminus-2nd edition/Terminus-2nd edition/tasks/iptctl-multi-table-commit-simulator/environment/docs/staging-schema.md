# Staging snapshot schema

`iptctl ingest` writes a JSON snapshot consumed by `iptctl export`. Export must read the snapshot and sibling merge-staging artifact — it must not re-parse the restore file or re-read phase modules from the environment.

## Top-level snapshot fields

| Field | Type | Rule |
|-------|------|------|
| `staging_version` | int | Always `1` |
| `restore_path` | string | Absolute path to the source `.v4` file |
| `restore` | string | Basename without `.v4` |
| `restore_digest` | string | SHA-256 hex of restore file bytes |
| `phase_config` | object | Resolved phase settings at ingest time (see below) |
| `tables` | object | Parsed table blocks from `rule_lexer.sh` |
| `binding` | object | `plan_digest` and `merge_staging_digest` |

## phase_config object

| Field | Meaning |
|-------|---------|
| `commit_order` | Full kernel table commit order resolved at ingest (for example `mangle`, `nat`, `filter`), including tables absent from the restore file |
| `policy_mode` | How `:CHAIN` counters are handled during export |
| `rule_counter_mode` | How `-A [pkts:bytes]` suffixes are handled |
| `mark_mode` | Whether committed mangle marks activate nat rules |
| `ct_mode` | How `conntrack_order` is assembled |

Mode semantics are defined across `/app/docs/iptables-save-contract.md` and `/app/docs/phase-config-contract.md`.

## Merge-staging sibling

For snapshot path `/app/state/foo.staging.json`, ingest also writes `/app/state/foo.staging.json.merge-staging.json` (append `.merge-staging.json` to the snapshot filename suffix) containing:

| Field | Rule |
|-------|------|
| `merge_staging_digest` | SHA-256 of canonical merge payload (see iptctl-commit-pipeline.md) |
| `table_names` | Sorted table names present in snapshot |

The snapshot `binding.merge_staging_digest` must match the sibling file. Export aborts with exit code **4** when the sibling is missing, digests disagree, or plan binding fails guard checks.

## Binding

`binding.plan_digest` is computed at ingest from restore bytes and the resolved `phase_config` frozen in the snapshot. During export, `export_gate.sh` recomputes the digest with the same frozen `phase_config` and restore file bytes — it must not re-read live phase modules or call `load_runtime_config()`.

`verify_staging_binding` in `export_gate.sh` may be invoked directly on any snapshot path. It validates binding consistency only (see `/app/docs/export-guard-contract.md`) and does not require `report_emit.sh` to be correct.
