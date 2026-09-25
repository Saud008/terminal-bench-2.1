# Gap fill rules

Applied per canonical topic after remap, before deadline scan and SQLite export.

## Scope

For each canonical topic, fill every missing integer seq between the present minimum and maximum inclusive.

## Synthetic row fields

| Field | Rule |
|-------|------|
| publish_ns | Strictly increasing when rows are sorted by seq within the topic |
| publish_ns interpolation | Linear between nearest original neighbors by seq; if only a lower neighbor exists, step 1 ns per seq toward higher seq; if only an upper neighbor exists, step 1 ns per seq toward lower seq |
| payload | Copy the lower neighbor payload bytes; if no lower neighbor, copy the upper neighbor |
| receive_ns | Equal to publish_ns before seed adjustment |
| seed adjustment | Add (seed mod 11) nanoseconds to publish_ns and receive_ns on each synthetic row; preserve strict per-topic publish_ns monotonicity by seq |
| synthetic flag | Set to 1 in SQLite export |

Do not drop gaps. Do not assign the same publish_ns to multiple synthetic rows by reusing the next original timestamp.
