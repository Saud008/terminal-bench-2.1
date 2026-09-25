# Submission explanations — redis-stream-consumer-group-journal-replay

**Task folder:** tasks/redis-stream-consumer-group-journal-replay/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents build redisctl in three milestones over an offline Redis Streams JSONL journal. Pending visibility, idle reclaim, MKSTREAM dollar ids, and export rollup interact across ingest, claim, group, and export packages. Partial work on one milestone passes bundled checks while hidden stream prefix journals and second export passes still fail. The decoy wrap package looks related but is not on the replay hot path.

## Solution Explanation

The oracle copies corrected Go sources into internal/claim, internal/group, and internal/export, then runs go build for /app/bin/redisctl. Milestone one defers pending_log until XACK replay. Milestone two fixes idle comparison and dollar tail ids. Milestone three exports distinct PEL counts and idempotent reclaim totals. Contracts live in /app/docs rather than the instruction prose.

## Verification Explanation

Each milestone test.sh rebuilds redisctl with go build before pytest. Twenty three tests call redisctl replay and export through subprocess and compare output to an independent reference_stream_state_machine in Python. Hidden tests set an environment stream prefix to rewrite stream keys. Stage file persistence and a second export pass check idempotency. NOP on the baseline image scores zero until all milestone patches are applied.
