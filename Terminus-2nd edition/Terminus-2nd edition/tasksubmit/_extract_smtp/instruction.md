Implement full SMTP header thread correlation for the mailindex CLI under /app/cmd/mailindex and /app/internal/. Extend the Go packages so that:

mailindex index --mail-dir DIR --thread-db SQLITE --output JSON

recursively discovers every .eml and .mbox file under the mail directory, skips malformed messages, deduplicates by Message-ID, correlates messages into threads, commits the rows in a single SQLite transaction, and writes a report that matches an independent reference with strict equality against the default fixture tree under /app/fixtures/mail and /app/data/thread.db. mailindex publish --output JSON must re-emit the report from the saved snapshot at /app/state/thread-index.snapshot.json without re-indexing.

Rebuild with go build -mod=readonly -o /usr/local/bin/mailindex ./cmd/mailindex from /app after edits. The Go compiler lives at /usr/local/go/bin/go; if an interactive shell reports go: command not found, export PATH=/usr/local/go/bin:${PATH} before building.

Do not edit anything under /app/fixtures/, /app/data/, or /tests/.

## Model field types (do not change)

Exported types in /app/internal/model/types.go are part of the contract. Preserve field names and types — especially MailMessage.InReplyTo as a string holding the first angle-bracket token from In-Reply-To (empty when absent). Union every References token during thread assign, but do not change InReplyTo to a string slice or merge References into it at parse time. Full parsing and threading rules are in /app/docs/thread-index-schema.md.

## Report JSON schema (strict equality)

The verifier compares the full export document. Use these exact top-level keys: index_version, files_read, messages_in, messages_indexed, messages_skipped_malformed, messages_deduped, threads_resolved, and messages_indexed_list. Each list entry requires message_id, thread_root_id, date_unix, subject, and is_root (JSON boolean).

messages_indexed_list length must equal messages_indexed. List order: date_unix ascending, then message_id ascending. Snapshot persistence, digest verification, rollback, deduplication, exit codes, and fixture layout are documented in /app/docs/fixture-catalog.md, /app/docs/thread-index-schema.md, and /app/docs/index-snapshot.md. Optional verifier-only mail bundles live under /opt/verifier-fixtures/ when TB3_SMTP_FIXTURES is set to that directory.
