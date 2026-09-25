# Mailsync mailbox-trust admission gate

You need an offline mailbox-trust admission tool that decides whether Maildir message trees may be trusted for sealed sync-report attestation on this host. The tool stages a tamper-evident mailbox snapshot, applies Message-ID authenticity, `:2,` flag-letter authenticity, tag-merge integrity, and SQLite-before-rename transaction gates, and publishes a digest-sealed sync-report attestation only when those gates hold. There is no remote mail server and no outbound network step.

mailsync at /usr/local/bin/mailsync is that tool. Operators run ingest to admit a Maildir tree, sync to apply the integrity gates over staged rows and notmuch tag state, and publish to seal the attestation.

## Operator surface

CLI verbs, flags, default paths, and TB3_MAILDIR verifier maildir roots live in /app/docs/cli-surface.md.

mailsync ingest must admit maildir `cur` and `new` (never `tmp`), stage /app/state/mail-sync.snapshot.json as the tamper-evident mailbox snapshot, and must not rename maildir files or write /app/output/mail-sync-report.json.

mailsync sync must enforce Message-ID authenticity dedupe, tag-merge integrity, Maildir flag-letter authenticity, and SQLite-before-rename transaction order before any on-disk flag suffix mutation, and must refuse sealed publish when authenticity gates are unset or drifted.

mailsync publish must reseal /app/output/mail-sync-report.json from the ledger plus on-disk staging snapshot only, never rescanning the mailbox or renaming files, and publish only after the integrity gates hold.

## Integrity policy

Field-level trust rules live in the docs below. Admission must enforce every gate before sealing:

- Message-ID authenticity and duplicate refusal: /app/docs/message-id-dedupe.md
- tag-merge integrity precedence: /app/docs/tag-precedence.md
- Maildir `:2,` flag-letter authenticity: /app/docs/maildir-flag-order.md
- SQLite-before-rename transaction integrity: /app/docs/sync-transaction-order.md
- tamper-evident staging snapshot layout: /app/docs/staging-snapshot.md
- snapshot-bound publish without mailbox rescan: /app/docs/snapshot-publish-bridge.md
- sealed sync-report attestation schema: /app/docs/export-schema.md

## Paths and fixtures

Primary artifacts are /app/state/mail-sync.snapshot.json (tamper-evident staging after admitted Maildir load) and /app/output/mail-sync-report.json (digest-sealed mailbox sync attestation). Bundled fixtures live under /app/fixtures; hidden verifier trees may appear under /opt/verifier-fixtures. Legacy export metadata decoration helpers are not on the ingest, sync, or publish trust-admission path. Use /app/scripts/reset-state.sh between cross-run checks. Do not edit /app/docs/, /app/fixtures/sources/, /opt/verifier-fixtures/sources/, or /tests/.

## Implementation

mailsync is implemented in Go under /app. Patch the Go packages there; the verifier recompiles via /app/scripts/verifier-rebuild.sh before pytest and overwrites /usr/local/bin/mailsync. Replacing the binary with Python or another language without updating the Go sources will not survive verification.
