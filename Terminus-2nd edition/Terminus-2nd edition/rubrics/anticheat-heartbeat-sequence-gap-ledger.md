# Platform rubric — anticheat-heartbeat-sequence-gap-ledger

**Task folder:** tasks/anticheat-heartbeat-sequence-gap-ledger/

Agent writes /app/state/gap-ledger-snapshot.json after each successful heartbeat batch, +3
Agent merges staged gap and ban counters with live session rejection fields at export, +3
Agent implements batch ingest with sequence gap open and in-grace close per gap-ledger.md, +3
Agent anchors session monotonic clock from bind per session-anchor.md, +3
Agent returns HTTP 400 for missing bind fields and unbound sessions on batch, +3
Agent returns HTTP 409 for duplicate sequences and skew violations outside tolerance, +3
Agent reads skew_rejections and duplicate_rejections from live session row at publish, +2
Agent rebuilds anticheatd with go build after editing heartbeat pipeline modules, +2
Agent leaves protected server wiring and contract docs unchanged, +1
Agent patches only export merge while ingest staging remains a no-op, -3
Agent derives rejection counters from snapshot file instead of live session row, -3
Agent modifies internal/api/server.go to bypass HTTP status boundary checks, -5
