# IPMI SEL binary layout

This document defines the on-disk SEL blob format consumed by sel-chain ingest.

## File header (8 bytes)

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Magic ASCII SEL1 |
| 4 | 2 | record_count, unsigned little-endian |
| 6 | 1 | record_length, unsigned byte — stride for each record in bytes (16 for standard system events) |
| 7 | 1 | header_xor — XOR of bytes 0 through 6 inclusive |

Ingest must reject files whose magic is not SEL1 or whose header_xor does not match.

## Standard system event record (16 bytes)

Each record occupies exactly record_length bytes from the header. The record cursor advances by record_length after each record.

| Offset | Size | Field |
|--------|------|-------|
| 0 | 2 | record_id, unsigned little-endian |
| 2 | 1 | record_type (0x02 = system event) |
| 3 | 4 | timestamp, unsigned little-endian Unix seconds |
| 7 | 2 | generator_id, unsigned little-endian |
| 9 | 1 | event_revision |
| 10 | 1 | sensor_type |
| 11 | 1 | sensor_number |
| 12 | 1 | event_dir_type — lower nibble is event_type, upper nibble is direction |
| 13 | 1 | event_data1 |
| 14 | 1 | event_data2 |
| 15 | 1 | record_xor — XOR of bytes 0 through 14 inclusive |

Only record_type 0x02 is ingested. Other types are skipped without counting as checksum failures.

## Sensor type naming

Bundled names live in /app/config/sensor-types.tsv as tab-separated hex_key and name (example: 0x07<TAB>Processor).

Additional sensor types documented only in the table below must still resolve during export:

| Hex | Name |
|-----|------|
| 0xC0 | OEM Power Unit |
| 0xC1 | OEM Memory Channel |
| 0xDC | Platform Security |

Lookup uses an uppercase hex key with 0x prefix (example: 0x0C).

## Severity rank

Severity is derived from event_type (lower nibble of event_dir_type):

| Rank | Severity label | event_type values |
|------|----------------|-------------------|
| 0 | critical | 0x01, 0x02, 0x03 |
| 1 | warning | 0x06, 0x07, 0x08 |
| 2 | info | all other values |

## Checksum order

Compute record_xor and compare to byte 15 before inserting into SQLite or updating ingest counters. Rejected checksum records must not appear in sel_records and must increment rejected_checksum in staging.

## Idempotency

record_id is the deduplication key. Re-ingesting a blob must not insert a second row with the same record_id; such rows increment duplicate_rejected instead.
