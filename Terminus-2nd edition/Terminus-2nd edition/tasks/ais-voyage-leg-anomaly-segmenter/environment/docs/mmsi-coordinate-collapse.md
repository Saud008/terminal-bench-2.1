# MMSI dedupe

During intake, collapse duplicate position reports before burst handling. Two rows are duplicates when they share the same mmsi, lat and lon rounded to six decimal places, and ts_epoch within AIS_MMSI_DEDUPE_SEC (default 2). Keep the row with the lowest seq; count each removed row toward duplicate_mmsi in atlas anomalies.

Dedupe keys must ignore station and sog. Apply dedupe before burst collapse.
