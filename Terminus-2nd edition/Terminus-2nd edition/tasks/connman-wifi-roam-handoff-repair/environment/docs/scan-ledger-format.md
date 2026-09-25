# Scan ledger format

One ledger row per scan.events entry in scenario order.

| Field | Type | Description |
|-------|------|-------------|
| event_index | integer | Zero-based index into scan.events |
| event_type | string | partial or full |
| coverage | number | coverage field from the event |
| credited | boolean | Whether this event credits handoff scan success |

## Credit rules

| Condition | credited |
|-----------|----------|
| event_type is full, coverage is at least 1.0, and every scan.required_bssids value appears in bssids_seen | true |
| event_type is partial | false |
| full scan missing a required bssid | false |

Partial scans never credit success even when coverage exceeds 0.5.

Only the first credited event sets scan_credited true; later events may still appear in the ledger with credited false.
