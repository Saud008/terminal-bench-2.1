# NMEA MMSI extraction

The nmea_raw field uses a simplified AIS VDM sentence. After splitting on commas, field index 5 (0-based) holds the payload. Within that payload, bytes at offsets 8..16 (inclusive start, exclusive end) are ASCII decimal digits forming the nine-digit MMSI.

Do not reinterpret those bytes as binary big-endian integers. The parsed integer must equal the JSONL mmsi field or ingest rejects the row.

Example payload field: 15MwkT0P00G?wflK?Kc<R@T4000000 — digits at the specified offsets must decode to the row MMSI.
