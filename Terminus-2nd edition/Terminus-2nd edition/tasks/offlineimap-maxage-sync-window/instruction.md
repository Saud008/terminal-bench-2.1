Mail-ops operators need a host-local offlineimap maxage sync-window control path that keeps folder-rule admission, maxage cutoff gates with timezone offsets, UIDVALIDITY ledger resets, dry-run state isolation, staging snapshot digests, and sealed sync export aligned across retries. Operate the offlineimap-audit CLI under /app so sync follows the ops contracts in /app/docs/spec.md, /app/docs/maxage-window.md, /app/docs/folder-filter.md, /app/docs/cache-ledger.md, /app/docs/staging-snapshot.md, and /app/docs/export-summary.md.

The offlineimap-audit driver at /app/bin/offlineimap-audit admits folder rules and message catalogs against Maildir trees and IMAP metadata, applies maxage cutoffs, maintains UIDVALIDITY ledgers at /app/state/sync-ledger.db, writes staging snapshots at /app/state/folder-snapshot.json and sync-run metadata at /app/state/sync-run.json, then publishes sealed export JSON under /app/output. The default export path for the basic-inbox scenario is /app/output/basic-inbox.json.

CLI contract:
- offlineimap-audit sync --mailbox-dir DIR --imap-meta PATH --folder-rules PATH --reference-epoch EPOCH --maxage-sec SECONDS --tz-offset MINUTES --export PATH
- --dry-run still writes export JSON but must not mutate /app/state/sync-ledger.db or create /app/state/sync-run.json
- folder filtering applies before manifest row selection, while /app/state/folder-snapshot.json still lists every IMAP folder with a selected flag

Cross-run contract:
- repeated syncs on unchanged inputs must produce stable exports
- UIDVALIDITY bumps reset the cached high-water UID for that folder before the next real sync writes new ledger state

The verifier may set TB3_FIXTURES_DIR to an alternate offlineimap fixture root with additional catalog and scenario trees. The same sync contracts must hold for those verifier-only fixtures.

The environment has no outbound network access. Do not edit /app/docs/ or /app/fixtures/.
