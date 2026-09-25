# CLI surface

Binary: `/usr/local/bin/mailsync`, built from Go sources under `/app` (`/app/go.mod`, `/app/cmd/mailsync`, `/app/internal/...`).

## Implementation language

Fixes must patch the Go tree under `/app`. The verifier runs `/app/scripts/verifier-rebuild.sh` before every pytest invocation; it recompiles `./cmd/mailsync` and **replaces** `/usr/local/bin/mailsync`. Agent edits in Python or other languages that do not update the Go sources are discarded at test time.

## ingest

```
mailsync ingest --maildir PATH --db PATH
```

Scan `cur` and `new`, write staging snapshot. Does not rename files or write the export report.

## sync

```
mailsync sync --maildir PATH --db PATH --report PATH
```

Full pipeline: ingest snapshot, dedupe, thread bind, tag merge, SQLite commit, maildir renames, report write.

## publish

```
mailsync publish --db PATH --report PATH
```

Read snapshot + database; write report without rescanning maildir or renaming files.

## Environment

`TB3_MAILDIR` when set to an absolute path replaces `--maildir` for verifier-only trees under `/opt/verifier-fixtures/`.

Exit 0 on success, 1 on usage error, 2 on data errors (malformed maildir skipped entries still allow exit 0 if at least one message indexes).
