# Ingest export pipeline

Stages:
1. Parse JSONL via internal/log
2. Restore checkpoint from /app/state/ckpt-<basename>.json when present
3. Apply ordered events via internal/replay (lease + dns + journal)
4. Write /app/state/lease-snapshot.json (staging)
5. Build lease-report.json (export)
6. Persist authoritative rows to SQLite at --db path

Replay driver invokes checkpoint persist on replay_checkpoint ops and must not persist checkpoints mid-event before DNS invalidation completes on IP-change ACK paths.

Journal tail in export contains the last eight journal entries with seq, op, ok, at_sec.

Export lease-report.json also includes tentative_count per /app/docs/lease-contract.md.
