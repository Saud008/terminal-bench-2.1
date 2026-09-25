# Platform rubric — dropcopy-session-bust-ledger

**Task folder:** tasks/dropcopy-session-bust-ledger/

Agent validates FIX body length and checksum before staging dropcopy events, +3
Agent sorts staging events by SendingTime then MsgSeq before replay, +3
Agent resets per-session MsgSeq baseline on logon rows with ResetSeqNumFlag Y, +3
Agent deduplicates replay inserts on ExecID tag 17 alone, +2
Agent applies trade bust ExecType H as signed reversal of referenced fill, +3
Agent lets ExecTransType correct supersede earlier cancel on same OrigClOrdID chain, +3
Agent wraps each JSONL stream file replay in one SQLite transaction with rollback, +3
Agent bumps replay-generation.json and gates export on generation match, +2
Agent exports compliance rollup with audit_digest over net positions and active exec ids, +2
Agent rebuilds dropcopyctl after editing ingest replay or export packages, +2
Agent patches checksum validation only while leaving seq reset baseline stale, -3
Agent sums duplicate ExecID rows using ClOrdID concatenation idempotency key, -3
Agent commits partial stream batch rows when later sequence regression fails, -3
Agent lets cancel ExecTransType win over later correct on same chain, -2
Agent exports compliance before replay generation gate is satisfied, -2
