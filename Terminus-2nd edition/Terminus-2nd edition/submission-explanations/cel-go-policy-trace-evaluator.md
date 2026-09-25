# Submission explanations — cel-go-policy-trace-evaluator

**Task folder:** tasks/cel-go-policy-trace-evaluator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must extend celctl so boolean AND and OR short-circuit side-effecting has() calls, nested cel.bind keeps outer frames until inner bodies finish, duration compares canonicalize to nanoseconds, map comprehensions keep the last colliding key, and trace export lists only evaluated branches. The contracts live in three docs under /app/docs and the bugs span internal eval, duration, and trace export while a decoy wrap module is not on the hot path. Fixing short-circuit alone still fails duration, bind scope, map merge, or trace branch counts on hidden nested-bind fixtures.

## Solution Explanation

The oracle copies corrected internal eval and duration packages into /app, rebuilds celctl, and leaves ingest and staging unchanged. Evaluation walks the staging AST with proper frame discipline and records branches only for operands that actually run. Duration comparison routes both sides through nanosecond canonicalization. Trace export reads the staging snapshot and writes result plus branch list and has_call_count to /app/output/trace.json.

## Verification Explanation

test.sh rebuilds celctl with go build before pytest. Twenty-three tests invoke celctl ingest and celctl eval with trace via subprocess. A Python reference_cel module recomputes expected results, branch counts, and has() side-effect totals. Bundled fixtures cover short-circuit, duration, map collision, and nested bind. Two hidden tests under /opt/verifier-fixtures exercise nested bind with AND short-circuit. NOP on the starter tree fails eight tests. Oracle passes all twenty-three.
