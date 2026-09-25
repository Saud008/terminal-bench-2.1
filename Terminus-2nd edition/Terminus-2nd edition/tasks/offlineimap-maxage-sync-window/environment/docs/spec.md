# offlineimap-audit specification

The driver command is:

    /app/bin/offlineimap-audit sync --mailbox-dir DIR --imap-meta PATH --folder-rules PATH \
      --reference-epoch EPOCH --maxage-sec SECONDS --tz-offset MINUTES \
      [--dry-run] --export PATH

Inputs:

- mailbox-dir: Maildir root (fixtures ship manifests beside maildirs; the driver reads messages.tsv from the scenario directory).
- imap-meta: JSON with account string and folders array (name, uidvalidity, uidnext).
- folder-rules: text file with include/exclude globs (see folder-filter.md).
- reference-epoch: UTC unix seconds anchoring the sync run.
- maxage-sec: age window length in seconds.
- tz-offset: signed integer minutes applied per maxage-window.md.
- dry-run: when set, perform selection math but skip persistent state (see export-summary.md).
- export: JSON summary path.

Pipeline order (mandatory):

1. Parse IMAP metadata and folder rules; build the eligible folder list before reading messages.
2. Publish folder snapshot JSON to /app/state/folder-snapshot.json (staging-snapshot.md).
3. Reset or validate UIDVALIDITY rows in /app/state/sync-ledger.db (cache-ledger.md).
4. Apply maxage cutoff to manifest rows whose folder is eligible (maxage-window.md).
5. Write export summary JSON (export-summary.md).
6. Unless dry-run, update ledger high-water UIDs and write /app/state/sync-run.json.

Manifest format (messages.tsv): tab-separated header row then folder, internal_date, size_bytes, uid. internal_date is UTC epoch seconds.

Environment variable OI_MAXAGE_OFFSET_SEC may add extra seconds trimmed from the window (maxage-window.md).
