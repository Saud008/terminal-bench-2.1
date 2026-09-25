# Gap findings and reconcile output

## Clock drift

Walk events in causal sort order. Maintain a frontier vector clock initialized empty.

For each event, compute expected as increment on a copy of the current frontier for the event sender. If expected does not equal the event vector_clock map (component-wise equality, missing keys count as zero), emit clock_drift with detail frontier_mismatch.

After each event, set frontier to the component-wise maximum merge of frontier and the event vector_clock.

## Clock gap

Walk causally sorted events. For each adjacent pair, for each node id present in either clock, if the absolute component delta exceeds max_gap, emit clock_gap.

Default max_gap is 5. Environment variable TB3_GAP_BIAS adds an integer bias to max_gap when set.

## Finding object

| Field | Type |
|-------|------|
| code | string |
| event_id | string |
| detail | string |

## reconcile-findings.json

| Field | Type |
|-------|------|
| scenario | string |
| finding_count | int |
| findings | array of finding objects sorted by event_id then code |

Finding codes: clock_drift, causal_violation, moderation_conflict, mute_leak, receipt_mismatch, duplicate_delivery, clock_gap.

## reconcile-revision.json

| Field | Type |
|-------|------|
| reconcile_revision | int | Increments by one on each successful reconcile |
