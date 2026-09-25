# Timestamp predicate

Catalog catalog_tz declares the evaluation zone for timestamp predicates. When catalog_tz is UTC, bounds passed with a Z suffix must parse and compare in UTC.

Local wall-clock interpretation of Z-suffixed bounds is incorrect. Measured_at row values are RFC3339 UTC strings and compare directly after UTC parsing.

Ts-gte filtering applies after row materialization when stats pruning kept the row group.
