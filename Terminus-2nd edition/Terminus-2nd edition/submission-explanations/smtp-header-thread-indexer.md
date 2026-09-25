# Submission explanations — smtp-header-thread-indexer

**Task folder:** tasks/smtp-header-thread-indexer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a multi-stage Go mailindex pipeline where MIME parsing, thread union, SQLite persistence, snapshot digest, and publish-from-snapshot all have to agree before strict JSON equality passes. Contracts are split across thread-index-schema.md, index-snapshot.md, and fixture-catalog.md, so fixing link.go alone still leaves digest or missing-database exit-code failures. Near-miss runs often stalled because go was not on PATH in interactive shells even though the compiler lives at /usr/local/go/bin/go; without a rebuild loop they could not iterate on the remaining implementation bugs. The task also punishes partial fixes with all-or-nothing scoring when bundled tests pass but hidden bracket-mail fixtures or snapshot traps still fail.

## Solution Explanation

The oracle copies golden Go sources into /app/internal and /app/cmd/mailindex, exports PATH to include /usr/local/go/bin, rebuilds mailindex, and runs index against the default fixture tree. Thread linking must union every References token while InReplyTo stays a single stored string. Snapshot writing computes index_digest only from messages_indexed_list row bytes, and store.Open must fail when the SQLite path is missing rather than creating an empty database. Publish reads the on-disk snapshot at /app/state/thread-index.snapshot.json and writes thread-index.json without re-querying SQLite or re-running assign.

## Verification Explanation

Pytest rebuilds the binary through test.sh with PATH and CGO exports, then drives mailindex via subprocess on fresh output paths. An independent reference implementation in the test module recomputes expected reports from the same fixtures and schema docs, so static JSON files cannot pass. Tests patch broken versus golden module sources to prove ingest-only and export-only failure modes stay independent. Hidden bracket-mail bundles and snapshot digest assertions catch agents who fix default fixtures but leave References union, digest scope, or missing-database handling wrong.
