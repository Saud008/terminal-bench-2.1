# Gate event contract

Gate events pair gate_in and gate_out event times per container. Events load in chronological order before SQLite insert.

## Fields

Each gate event row contains container_id, event (gate_in or gate_out), and ts ISO-8601 event time.

## Dwell window

Billable calendar span starts at gate_in date inclusive. It ends at gate_out date exclusive when gate_out exists. When gate_out is absent, billing_through from scenario metadata is the exclusive end date.

## Sorting

yardbundle event sorting must preserve chronological order so gate_in precedes gate_out for dwell pairing.
