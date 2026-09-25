# Export schema

Export version 1 written by commit (and by reconcile after prepare):

| Field | Type | Meaning |
|-------|------|---------|
| export_version | int | Always 1 |
| scenario | string | Scenario label from prepare seal |
| seed | string | Seed from prepare seal |
| releases_attempted | int | Total release rows processed |
| releases_succeeded | int | Successful file moves |
| releases_failed | int | Failed releases |
| duplicate_skipped | int | Idempotent duplicate skips |
| ledger_tail_sequence | int | Highest assigned release sequence |
| release_epoch | int | Bumped reconcile epoch from staging (must match `/app/state/release-epoch.json`) |
| policy_digest | string | Copied from staging policy_digest for this reconcile (see `/app/docs/release-policy.md`) |
| prepare_fingerprint | string | Copied from /app/state/prepare-seal.json (see /app/docs/custody-chain.md) |
| custody_root | string | Digest of custody journal receipts (see `/app/docs/custody-chain.md`) |
| pending_in_spool | object | Maps spam and virus to sorted quarantine ids still on spool |
| release_log | array | Per-attempt outcomes in processing order |

pending_in_spool must exclude quarantine ids whose ledger entry has status released. When /app/state/release-staging.json exists, derive pending from its pending_in_spool map minus released ids. Do not count msg.*.eml files under /app/work/released/ as pending even if they remain on disk.

release_epoch must equal the `release_epoch` field written into release staging for this reconcile, and that value must match the persisted epoch file. Do not copy `ledger_tail_sequence` into `release_epoch`.

policy_digest must equal the `policy_digest` field on release staging for the same reconcile.

prepare_fingerprint must equal the prepare seal value for this prepare. Do not recompute it only from commit-time arguments.

custody_root must match `/app/docs/custody-chain.md` for the journal written during this commit.

release_log rows use status released, failed, or duplicate_skipped in request processing order. sequence is null unless status is released.
