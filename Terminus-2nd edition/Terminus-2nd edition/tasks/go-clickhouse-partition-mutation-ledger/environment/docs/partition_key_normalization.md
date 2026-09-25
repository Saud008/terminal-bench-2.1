# Partition key normalization

partition_id for a metadata row is derived as:

table_name followed by pipe-separated key=value pairs sorted by **column name ascending**.

Example: table events with keys {month: "2024-01", region: "eu"} becomes:

events|month=2024-01|region=eu

Column order must follow lexicographic column name order, not value order or insertion order.
