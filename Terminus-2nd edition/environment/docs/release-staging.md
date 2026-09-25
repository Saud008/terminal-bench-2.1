# Release staging

After ingest, reconcile writes `/app/state/release-staging.json` before processing release rows.

| Field | Meaning |
|-------|---------|
| staging_written | Must remain false for a normal ingest staging pass |
| release_epoch | Current bumped value from `/app/state/release-epoch.json` (see `/app/docs/epoch-schema.md`) |
| policy_digest | Digest of present hold_token values at staging time (see `/app/docs/release-policy.md`) |
| prepare_fingerprint | Written by prepare after staging (see `/app/docs/custody-chain.md`) |
| pending_in_spool | Quarantine ids still on spool grouped by stored class from the manifest |
| index | Map of quarantine id to stored_class and spool_subdir |

Export pending counts must be derived from this staging snapshot plus ledger released ids, not by scanning `/app/work/released/`.

The manifest at `/app/state/spool-manifest.json` records `stored_class` from each meta file and `spool_subdir` for the physical spool directory copied during ingest. Locate must honor `spool_subdir` when the message file is not under the request class directory.
