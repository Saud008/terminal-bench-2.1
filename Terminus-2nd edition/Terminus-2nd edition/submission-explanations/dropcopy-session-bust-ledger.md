# Submission explanations — dropcopy-session-bust-ledger

**Task folder:** tasks/dropcopy-session-bust-ledger/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a drop-copy lifecycle engine where protocol sequencing, execution semantics, and SQLite persistence interact. The CLI surface is asymmetric: ingest requires --seed and optional --fixture-dir; replay takes only --scenario and reads staging; export takes --output plus optional --fixture-dir for overlay compatibility. Sequence reset logons change the MsgSeq baseline, so replay must accept low sequence numbers only after reset_seq staging rows. ExecID-only idempotency, trade bust reversals, and cancel versus correct precedence are separate modules; fixing one layer still fails hidden rollback or generation-gate tests. Each successful replay must bump staging and the replay-generation.json object ({"replay_generation": N}) together, including a second replay without re-ingest, while persisting committed rows in the ledger_rows SQLite table. Each JSONL stream file must commit atomically, so partial replay leaves the database unchanged when any row violates sequence rules. Hidden fixtures shift MsgSeq with TB3_SEQ_BIAS and include invalid checksum rows that must fail ingest without durable staging.

## Solution Explanation

The oracle copies golden ingest, replay, and export modules that validate wire form, write sorted staging snapshots, replay stream batches inside SQLite transactions into ledger_rows, and export compliance JSON after generation checks. ingest normalizes pipe-delimited fixtures, validates checksums, and records reset_seq on 141=Y logons. replay tracks per-session sequence state, skips duplicate ExecIDs, applies bust and cancel/correct precedence against OrigClOrdID chains, and bumps /app/state/replay-generation.json as {"replay_generation": N}. export reads net positions and active ExecIDs from /app/work/dropcopy.db and emits audit_digest from canonical JSON. dropcopyctl is rebuilt from /app after patching the golden Go sources.

## Verification Explanation

Pytest drives dropcopyctl ingest, replay, and export subprocess commands against bundled and hidden JSONL streams with an independent reference_replay.py engine. Tests assert staging sort order, bust net-zero positions, correct-over-cancel net qty, ExecID duplicate suppression, SQLite rollback on sequence failure, generation persistence gates, and TB3 hidden sequence bias traps. test.sh rebuilds dropcopyctl before pytest. Oracle reward requires all behavioral tests with golden module patches applied.
