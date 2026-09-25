# Submission explanations — java-flink-checkpoint-barrier-skew-chronicle

**Task folder:** tasks/java-flink-checkpoint-barrier-skew-chronicle/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task builds a three-stage Flink checkpoint skew chronicle in Java. Behavior is split across alignment semantics, watermark precedence, chained-operator boundaries, and per-attempt dedupe contracts in /app/docs/. Fixing one module often passes bundled output while skew math, hidden traps, or retry attempts still fail.

## Solution Explanation

The oracle patches five Java modules and installs a rebuilt flink-skew.jar. The fix aligns operator mapping, unaligned classification, watermark guards, chain deduplication, and per-attempt dedupe keys with the doc contracts. All three CLI stages must run in order to produce the chronicle JSON.

## Verification Explanation

test.sh rebuilds the jar then runs 23 pytest functions that spawn java -jar /app/bin/flink-skew.jar. skew_refmath.py recomputes artifacts from fixtures. Hidden packs under /opt/verifier-fixtures exercise unaligned-only and chained-only jobs. NOP on the broken tree fails skew and trap checks while the oracle passes all tests.
