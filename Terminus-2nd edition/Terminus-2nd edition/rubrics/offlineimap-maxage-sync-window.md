# Platform rubric — offlineimap-maxage-sync-window

**Task folder:** tasks/offlineimap-maxage-sync-window/
**Written:** 2026-06-25T17:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent applies folder include/exclude rules before maxage cutoff selection, +3
Agent computes maxage cutoff with tz offset and OI_MAXAGE_OFFSET_SEC env, +3
Agent resets high_uid when UIDVALIDITY changes in sqlite ledger, +3
Agent writes folder-snapshot.json with selected flag per folder, +2
Agent sums export synced_bytes from message sizes not message counts, +2
Agent skips ledger and sync-run writes on dry-run sync, +2
Agent sorts export folders list ascending in summary JSON, +2
Agent rebuilds and validates Bash and awk modules under /app/lib/offlineimap before exercising offlineimap-audit sync, +2
Agent hardcodes export JSON without running offlineimap-audit sync, -3
Agent applies maxage before folder filter reversing doc order, -3
Agent keeps stale high_uid after UIDVALIDITY bump, -2
Agent mutates sqlite ledger during dry-run sync, -2
Agent uses message count instead of byte sum in export totals, -2
