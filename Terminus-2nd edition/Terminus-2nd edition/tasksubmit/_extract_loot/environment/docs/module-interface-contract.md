# Authenticity-policy layer compatibility

Admission, anti-replay, and attestation policy layers under `/app/crates/lootsettle-core/src/` must remain mutually compatible so envelope authenticity, pool-epoch binding, pity carryover, duplicate conversion, idempotent replay, staging digests, and sealed export continue to compose on one settlement path. Verifier authenticity checks may exercise individual policy layers while neighboring layers stay on the working baseline; keep the shared settlement surface usable across those mixes.

## Compatibility requirements

Preserve all of the following across `/app/crates/lootsettle-core/src/lib.rs`, nested `mod.rs` files, submodule `.rs` sources, and `/app/crates/lootsettle-cli/src/main.rs`:

1. Public module layout. `lib.rs` must continue to expose the same public mods (decoy, duplicate, envelope, export, idempotent, ingest, model, pity, pipeline, pool, replay, staging) and the same crate-level re-exports (`run_export`, `run_ingest`, `run_settle`, `write_report`, `run_replay`).
2. Callable entry points used across authenticity layers must keep names, argument types, and return types compatible, including `canonical_body_json`, `verify_event_signature`, `apply_season_carryover`, `apply_pity_after_pull`, `validate_pool_epoch`, `process_grant`, `already_processed`, `record_processed`, `duplicate_skip_audit`, `sort_events`, `compute_events_digest`, `build_staging`, `verify_staging_digest`, `build_report`, `compute_settlement_digest`, `sorted_report_json`, `audit_processing_order`, and the pipeline runners.
3. Shared type compatibility. Types in `model.rs` such as `PullEvent`, `SeasonConfig`, `PlayerLedger`, `StagingSnapshot`, `PityLedgerFile`, `GenerationFile`, `SettlementReport`, `ProcessedEventsFile`, and `AuditEntry` must remain usable by other layers without breakage when only some policy files differ.
4. Module declaration paths. `pool/mod.rs` and `replay/mod.rs` must keep submodule declarations and `pub use` re-exports that sibling layers and the CLI rely on.

## Policy layer paths

| Logical layer | Path under `/app/crates/lootsettle-core/src/` |
|---------------|-----------------------------------------------|
| envelope | envelope.rs |
| pity | pity.rs |
| pool | pool/mod.rs |
| duplicate | duplicate.rs |
| idempotent | idempotent.rs |
| staging | staging.rs |
| export | export.rs |

Do not reshape the shared authenticity surface so that a mixed tree of agent policy layers and baseline layers fails to compose through `lootsettle`.
