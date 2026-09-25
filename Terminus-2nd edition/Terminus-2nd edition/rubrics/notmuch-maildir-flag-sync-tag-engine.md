# Platform rubric — notmuch-maildir-flag-sync-tag-engine

**Task folder:** tasks/notmuch-maildir-flag-sync-tag-engine/

Agent preserves X-Keywords in staging snapshot entries during ingest, +3
Agent bumps staging_epoch after SQLite commit and mirrors it in snapshot and report, +3
Agent commits SQLite before Maildir flag renames per sync-transaction-order.md, +3
Agent normalizes Maildir flag letters to canonical FSRDT order in reports, +3
Agent selects duplicate Message-ID winner by mtime and folder rank not lexicographic path, +3
Agent merges tags with X-Keywords winning over stored DB keyword tags, +3
Agent overlays snapshot x_keywords during publish when DB keyword tags are stale, +3
Agent binds In-Reply-To and References into shared thread_id clusters, +2
Agent re-exports publish reports without rescanning or renaming maildir files, +2
Agent rebuilds mailsync after editing internal Go packages, +2
Agent leaves /app/docs and bundled fixtures unchanged, +2
Agent drops x_keywords from staging snapshot rows during ingest, -3
Agent renames Maildir files before database commit completes, -3
Agent skips staging_epoch increment on successful sync, -3
Agent lets DB keyword tags override non-empty X-Keywords headers, -3
Agent picks cur/ duplicate over newer new/ copy for same Message-ID, -2
