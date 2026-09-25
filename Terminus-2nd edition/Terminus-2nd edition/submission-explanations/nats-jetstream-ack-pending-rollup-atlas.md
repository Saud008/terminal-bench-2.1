# Submission explanations — nats-jetstream-ack-pending-rollup-atlas

**Task folder:** tasks/nats-jetstream-ack-pending-rollup-atlas/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents build natsctl to replay offline JetStream journals into a staging snapshot and export per-consumer ack-pending rollups. Five behaviors interact across ack pending, redelivery scheduling, consumer filter subjects, Term purge on max deliver, and rollup high-water marks. Contracts are split across four docs under /app/docs. Fixing Ack order alone still fails NAK tick timing, filter glob traps, Term purge, or export high-water on hidden subject-prefix journals. A decoy rollup package is not on the export hot path.

## Solution Explanation

The oracle copies corrected filter, ack, redelivery, replay term, and export rollup Go sources into /app and rebuilds natsctl. Replay maintains ack-pending maps with AckSync gating, monotonic tick NAK scheduling, segment-wise filter matching, and Term purge when max deliver is exhausted. Export reads /app/state/nats-jetstream-stage.json and writes pending-rollup.json with per-consumer high_water_seq and redelivery_due counts.

## Verification Explanation

test.sh runs go build then twenty pytest cases via subprocess natsctl replay and export. A Python jetstream_reference_replay model recomputes staging and rollup expectations independently. Bundled JSONL journals cover AckSync, NAK ticks, filter glob, Term, and multi-consumer high water. Two hidden tests mutate subject prefixes per run. NOP on the starter tree fails eleven tests. Oracle passes all twenty.
