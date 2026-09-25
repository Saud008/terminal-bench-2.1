# Submission explanations — notmuch-maildir-flag-sync-tag-engine

**Task folder:** tasks/notmuch-maildir-flag-sync-tag-engine/
**Platform form only** — not in upload zip.

**Doc fix (2026-07-27):** Defined `tag_writes == messages_indexed` (including publish), `messages_in` vs deduped `entries`/`messages_indexed`, raw Message-ID `thread_id` format, and mandatory Go implementation with verifier-rebuild overwrite — addressing agents that passed 19/20 on an undocumented counter/implementation rule.

## Difficulty Explanation

Agents must wire a three-stage mailsync pipeline where ingest writes a staging snapshot, sync commits SQLite before maildir renames, and publish recombines database rows with snapshot metadata without rescanning disk. Six interacting Go modules disagree on flag normalization, dedupe winner selection, tag precedence, snapshot keyword retention, staging_epoch persistence, and publish overlay logic documented across staging-snapshot, snapshot-publish-bridge, sync-transaction-order, and tag-precedence contracts. Fixing export commit order alone leaves ingest x_keywords null and publish blind to snapshot keywords, while a staging-only fix still fails hidden TB3 duplicate winners and cross-run epoch monotonicity checks. Platform trials showed agents often reach nineteen of twenty tests then miss the single staging writer field copy, which is easy to overlook when auditing louder behavioral modules first. The decoy export wrap helper and staging validate module sit off the hot path and mislead agents who patch obvious export files without reading snapshot-publish-bridge.

## Solution Explanation

The oracle replaces seven Go sources covering maildir flag order, tag merge precedence, thread dedupe comparator, staging snapshot writer, export publish ordering with epoch bump, and syncengine ingest sync publish orchestration including snapshot keyword overlay. After copying golden files the solver rebuilds mailsync, resets fixtures, and runs a full sync against the bundled maildir. Commit-before-rename, FSRDT normalization, Better-based dedupe, X-Keywords precedence, snapshot x_keywords copy, post-commit staging_epoch increment, and publish overlay from snapshot entries are applied together so bundled and hidden verifier trees agree with the Python reference. Sync rewrites the staging snapshot after bumping epoch so publish and report share the same staging_epoch integer. Publish walks snapshot entries to re-merge tags when x_keywords are present even if SQLite keyword columns were cleared during testing or partial runs.

## Verification Explanation

Pytest rebuilds Go via verifier-rebuild.sh before every test, then drives mailsync ingest, sync, and publish through subprocess with independent reference_maildir.py recomputing expected reports. Twenty-eight behavioral tests assert SQLite persistence, export and snapshot paths, staging_epoch bumps across consecutive syncs, publish keyword overlay after deliberate DB corruption, TB3 hidden maildir semantics, and protected doc or fixture hashes. Hidden fixtures under /opt/verifier-fixtures exercise duplicate winners and publish epoch carryover with failure modes distinct from the public maildir tree. Reset-state.sh restores maildir seeds and database backups between cases so partial fixes cannot pass on stale on-disk state. Reference helpers bump staging_epoch the same way sync must, and publish reference overlay recomputes tags from snapshot x_keywords independently of the CLI implementation.
