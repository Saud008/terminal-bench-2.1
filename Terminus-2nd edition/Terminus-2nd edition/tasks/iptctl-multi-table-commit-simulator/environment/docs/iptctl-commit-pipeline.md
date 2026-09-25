# Ingest → export pipeline

`iptctl` implements a two-stage pipeline. `simulate` chains both stages.

## Commands

```text
iptctl ingest  --restore <file.v4> --snapshot <staging.json>
iptctl export  --snapshot <staging.json> --seed <seed> --export <report.json>
iptctl simulate --restore <file.v4> --seed <seed> --export <report.json>
```

## Stage 1 — ingest

1. `rule_lexer.sh` validates and materializes parsed tables.
2. Phase modules (`table_commit_order.sh`, `chain_policy_mode.sh`, `rule_counter_mode.sh`, `nat_mark_bridge.sh`, `ct_order_mode.sh`) resolve runtime configuration.
3. `plan_binding.sh` computes `plan_digest`.
4. `merge_stage_writer.sh` writes the merge-staging sibling and validates digest alignment.

Missing restore files exit **2** without writing a snapshot.

## `simulate` command

`simulate` runs ingest then export in one invocation. Failure handling is **not** identical to standalone `ingest` for every error mode.

### Missing restore file

| Command | Snapshot written? | Report written? | Process exit |
|---------|-------------------|-----------------|--------------|
| `iptctl ingest` | No | N/A | **2** |
| `iptctl simulate` | No | Yes — minimal report at `--export` | **2** |

For `simulate`, when the restore path does not exist, `report_emit.sh` writes a report matching `/app/docs/export-schema.md` with `exit_code` **2**, empty `commit_order`, `policies`, `rules`, and `conntrack_order`, and `restore` set to the basename of the missing path (without `.v4`). The process exit status must equal `exit_code` in the report. Ingest-stage failures after a restore exists still follow ingest rules (no snapshot; `simulate` does not emit a success-shaped report).

## Stage 2 — export

1. `export_gate.sh` verifies plan binding against frozen `phase_config` and merge-staging alignment (exit **4** on failure). This guard checks only whether the frozen staging snapshot is internally coherent; it must not hardcode phase literals or depend on `report_emit.sh` producing the final report correctly.
2. Export reads **only** the snapshot (tables + frozen `phase_config`) via the internal engine export path.
3. Export must **not** re-parse the restore file or consult live phase module output.

Environment variables set during ingest are **not** authoritative for export.

## Merge-staging digest payload

Canonical payload hashed into `merge_staging_digest`:

```json
{
  "staging_version": 1,
  "restore_digest": "<sha256>",
  "phase_config": { "...": "..." },
  "table_names": ["filter", "mangle", "nat"],
  "rule_counts": { "filter": 3, "mangle": 1, "nat": 2 },
  "policy_counts": { "filter": 2, "mangle": 1, "nat": 1 }
}
```

Keys sorted; compact JSON (`separators=(",", ":")`).

## Module map

| Module | Stage | Role |
|--------|-------|------|
| `rule_lexer.sh` | ingest | Parse restore to intermediate tables |
| `table_commit_order.sh` | ingest | Resolve commit order |
| `chain_policy_mode.sh` | ingest | Resolve policy counter mode |
| `rule_counter_mode.sh` | ingest | Resolve rule counter mode |
| `nat_mark_bridge.sh` | ingest | Resolve mangle→nat mark mode |
| `ct_order_mode.sh` | ingest | Resolve conntrack ordering mode |
| `plan_binding.sh` | ingest | Plan digest binding |
| `merge_stage_writer.sh` | ingest | Merge-staging sibling I/O |
| `export_gate.sh` | export | Pre-export binding validation |
| `report_emit.sh` | export | Snapshot-only simulation export |
| `ingest.sh` | ingest | Orchestration |
| `simulate.sh` | both | `simulate` command orchestration |
