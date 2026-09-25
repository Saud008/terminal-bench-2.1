# Module API

| Module | Functions |
|--------|-----------|
| common.sh | Path anchors and helpers (see Path anchors below) |
| parse_log.sh | extract_quarantine_id — sets PARSED_QID and PARSED_QUEUE_ID |
| queue_route.sh | locate_message — sets SPOOL_DIR, MSG_EML, MSG_META for class |
| release.sh | attempt_release — sets RELEASE_OK, DUPLICATE_SKIPPED |
| ledger.sh | init_ledger, record_release_attempt, ledger_tail_sequence |
| ingest.sh | ingest_scenario — copies spool, writes /app/state/spool-manifest.json |
| epoch.sh | bump_release_epoch, read_release_epoch — persists /app/state/release-epoch.json |
| staging.sh | write_release_staging — writes /app/state/release-staging.json after ingest |
| policy.sh | check_release_policy, compute_policy_digest, expected_hold_token — see /app/docs/release-policy.md |
| custody.sh | init_custody_journal, append_custody_receipt, compute_custody_root, write_prepare_seal, read_prepare_seal — see /app/docs/custody-chain.md |
| export.sh | init_session_state, append_session_json, emit_export |
| pipeline.sh | run_prepare, run_commit, run_reconcile |

wrap.sh under lib/decoy/ is a legacy helper and is not called by reconcile.

## Path anchors

/app/lib/common.sh must define these absolute path variables as part of the working baseline:

| Variable | Value |
|----------|-------|
| SPAM_SPOOL | /app/work/spool/spam |
| VIRUS_SPOOL | /app/work/spool/virus |
| RELEASED_SPAM | /app/work/released/spam |
| RELEASED_VIRUS | /app/work/released/virus |
| LEDGER_PATH | /app/work/ledger.json |
| MANIFEST_PATH | /app/state/spool-manifest.json |
| STAGING_PATH | /app/state/release-staging.json |
| EPOCH_PATH | /app/state/release-epoch.json |
| SEAL_PATH | /app/state/prepare-seal.json |
| CUSTODY_JOURNAL_PATH | /app/state/custody-journal.jsonl |
| STATE_PATH | /app/work/session-state.json |

Spam class routes to /app/work/spool/spam. Virus class routes to /app/work/spool/virus. Released files move under /app/work/released/CLASS/.
