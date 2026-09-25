# Thread index schema

## Parsed message model

Each indexed message is represented by `model.MailMessage` in `/app/internal/model/types.go`. Field types are part of the contract — do not change them.

| Field | Type | Meaning |
|-------|------|---------|
| `MessageID` | `string` | Literal angle-bracket token from `Message-ID` |
| `InReplyTo` | `string` | Single literal angle-bracket token from `In-Reply-To` (first match only; empty when absent) |
| `References` | `[]string` | Every angle-bracket token from `References`, in header order |

## Message-ID angle-bracket tokens

Match each ID with the `<...>` substring from the raw header value. Store the matched token **exactly** — including the leading `<` and trailing `>` — in `MessageID`, `InReplyTo`, and each `References` entry. You may trim ASCII whitespace around the matched token; do **not** strip the brackets, parse with `mail.ParseAddress` for storage, or persist bare addr-spec strings such as `thread-a@example.com`. Thread keys, SQLite rows, and JSON export must use the same literal tokens the reference parser extracts.

Parsing stores **one** token in `InReplyTo`, not a slice. When `In-Reply-To` contains multiple angle addresses, keep only the first matched `<...>` token. Do **not** merge `References` tokens into `InReplyTo` during parse. Implementation lives in `mailparse/parse.go`.

## Thread union (assign stage)

Thread linking runs in `thread/link.go`; root selection runs in `thread/root.go`; `thread/assign.go` orchestrates both. When building thread components, union the message with **every** batch-known Message-ID referenced by:

1. its non-empty `InReplyTo` string, and
2. **each** entry in `References`

Use all References tokens at assign time — not only the first — but keep `InReplyTo` as a single string field throughout parse and assign.

## Thread root selection

`thread/root.go` picks the thread root within each connected component: the message with the earliest parsed `Date`. Break timestamp ties with the lexicographically smaller `Message-ID`. Set `is_root` true only when `message_id` equals that root.

## Report and database

`/app/output/thread-index.json` includes counters plus `messages_indexed_list` (every indexed message once, sorted by `date_unix` ascending then `message_id` ascending). List length must equal `messages_indexed`.

### Required top-level JSON keys

Preserve these exact names in `model.Report` and the export JSON:

| JSON key | Type | Meaning |
|----------|------|---------|
| `index_version` | int | schema version (always `1`) |
| `files_read` | int | mail files discovered |
| `messages_in` | int | parsed messages before dedup |
| `messages_indexed` | int | rows written / list length |
| `messages_skipped_malformed` | int | parse failures |
| `messages_deduped` | int | duplicate Message-IDs dropped |
| `threads_resolved` | int | distinct thread components |
| `messages_indexed_list` | array | indexed message objects |

Each list entry requires `message_id`, `thread_root_id`, `date_unix`, `subject`, and `is_root` (JSON booleans). Do not rename fields or emit alternate counter names such as `threads_total` or `malformed_skipped`.

The JSON keys map one-to-one onto `model.Report` Go fields:

| JSON key | Go field (`model.Report`) |
|----------|---------------------------|
| `index_version` | `IndexVersion` |
| `files_read` | `FilesRead` |
| `messages_in` | `MessagesIn` |
| `messages_indexed` | `MessagesIndexed` |
| `messages_skipped_malformed` | `MessagesSkippedMalformed` |
| `messages_deduped` | `MessagesDeduped` |
| `threads_resolved` | `ThreadsResolved` |
| `messages_indexed_list` | `MessagesIndexedList` |

## Deduplication

When the same Message-ID appears more than once, keep exactly one message:

- **Across files:** keep the message from the lexicographically later relative POSIX path (for example `010-second.eml` wins over `001-first.eml`).
- **Within one `.mbox` file:** keep the last message in file order.

Dropped duplicates are counted in `messages_deduped`.

## CLI exit codes

`mailindex index` validates `--mail-dir` before indexing:

- Exit **2** when the mail path is missing, or exists but is not a directory (for example a regular `.eml` file).
- Exit **1** when the thread database cannot be opened or updated.
- Exit **0** only after the JSON report is written and the SQLite batch commits successfully.

**Missing database path:** the `go-sqlite3` driver **creates** a new SQLite file when `sql.Open` targets a path that does not exist. Before opening, verify that `--thread-db` already exists on disk (for example with `os.Stat`) and exit **1** when it is absent. Do not rely on `sql.Open` alone to detect a missing database.

After SQLite commit, write `/app/state/thread-index.snapshot.json` per `/app/docs/index-snapshot.md`. Publish export JSON from that snapshot only.

`message_threads` rows are inserted or replaced inside one SQLite transaction. Roll back and exit **1** on any indexed-row failure; do not leave partial rows or write the JSON report after a failed commit.
