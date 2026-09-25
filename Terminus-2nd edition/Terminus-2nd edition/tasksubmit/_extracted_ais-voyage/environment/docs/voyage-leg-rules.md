# Voyage leg rules

Segment each mmsi independently on atlas after speed suppression. Stable point order is mmsi ascending, ts_epoch ascending, seq ascending; count rows reordered relative to snapshot file order toward out_of_order anomalies.

Start a new leg when any of the following holds for the current point versus the previous kept point in the same mmsi (except the first point): port label changes including entry or exit via none, or draught delta meets draught-leg-boundaries.md threshold, or ts_epoch gap exceeds AIS_MAX_GAP_HOURS (default 12) converted to seconds.

Leg ids are formatted as {mmsi}-L{ordinal} with ordinal starting at 1 per mmsi. Each leg records start_ts and end_ts as RFC3339 Z from first and last kept points, point_count, start_port and end_port labels, and ports visited in order of first appearance within the leg without duplicates.

Atlas voyage_legs sorted by mmsi ascending then leg ordinal ascending.
