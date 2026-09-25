Build a quarantine release governance capability on the working amavis baseline under /app so reconcile produces security analysis artifacts: a release ledger, reconcile epoch, staging snapshot, prepare seal, custody journal, and export report used for hold-token release policy and custody-chain review.

Implement each /app/lib/ module against the contracts in /app/docs/quarantine-contract.md, /app/docs/release-policy.md, /app/docs/release-staging.md, /app/docs/custody-chain.md, /app/docs/export-schema.md, /app/docs/epoch-schema.md, and /app/docs/module-api.md. Hold token, policy digest, prepare fingerprint, and class-dependent custody receipt rules are defined only in those docs.

The CLI entrypoint is /app/bin/amavis-quarantine with prepare, commit, and reconcile
Staging is written to /app/state/release-staging.json
Epoch is written to /app/state/release-epoch.json
Prepare seal path is /app/state/prepare-seal.json
Custody journal path is /app/state/custody-journal.jsonl
Export JSON is written to the path passed as --export

Path anchors in /app/lib/common.sh for the spam spool, virus spool, released spam and virus directories, ledger, spool manifest, release staging, release epoch, prepare seal, custody journal, and session state are part of the working baseline contract.

amavis-quarantine reconcile --scenario NAME --seed SEED --export /app/output/report.json
