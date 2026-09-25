# Legacy staging bindings (deprecated)

Older sysctlmerge builds wrote merge-staging digests through `/app/lib/bind.sh` using `legacy_staging_digest`, hashing only the snapshot `effective` map for speed.

That helper remains in the tree for backward compatibility with offline tooling. **Do not use it for new ingest or export paths.**

Authoritative snapshot binding for merge-staging, replay ledger, and apply export is defined in `/app/docs/digest-contract.md` via `/app/lib/digest.sh` function `canonical_snapshot_digest`. Staging writers must delegate to that function rather than duplicating digest math or calling legacy helpers.
