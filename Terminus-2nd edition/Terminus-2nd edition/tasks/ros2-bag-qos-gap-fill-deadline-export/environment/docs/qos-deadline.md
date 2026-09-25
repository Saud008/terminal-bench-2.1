# QoS deadline evaluation

Evaluated after gap fill on consecutive same-topic messages ordered by seq.

## Clock

Use publish_ns spacing when topics.*.deadline_clock is publish.

## Effective threshold

Let speed default to 1.0 when the CLI --speed value is zero or negative.

| Symbol | Definition |
|--------|------------|
| deadline_ms | Configured value from metadata.json topics.*.deadline_ms for the canonical topic |
| effective_deadline_ms | max(1, ceil(deadline_ms / speed) - (seed mod 5)) |
| limit_ns | effective_deadline_ms * 1_000_000 |

Do not multiply deadline_ms by speed. Divide deadline_ms by speed before ceiling.

## Miss detection

For each consecutive pair (prev, cur) on the same canonical topic ordered by seq, a miss is recorded on cur when:

delta_ns = cur.publish_ns - prev.publish_ns

delta_ns > limit_ns

## deadline_misses.deadline_ms column

Stores the configured metadata deadline_ms for the topic, not effective_deadline_ms.

| Column | Source |
|--------|--------|
| topic | Canonical topic |
| seq | seq of the later message in the pair |
| delta_ns | cur.publish_ns - prev.publish_ns |
| deadline_ms | topics.*.deadline_ms from bag metadata |
