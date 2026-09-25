# FIT lap contract

`fitlap decode <fit-file>` validates the FIT-like stream CRC and applies decode-only lap alignment checks before lap parsing completes.

Binary stream format:

- Magic: bytes `FITL`
- Version: `u8` (must be `1`)
- Lap count: `u8`
- Lap rows: repeated fixed-width records
- CRC trailer: little-endian `u16` over all bytes before the trailer

Lap record layout (24 bytes):

- `start_time`: little-endian `u32`
- `end_time`: little-endian `u32`
- `distance_m`: little-endian `u16`
- `trigger_code`: `u8` (`0=manual`, `1=time`, `2=distance`, `3=session-end`)
- `note_len`: `u8` (0..12)
- `note_bytes`: 12-byte slot; UTF-8 text occupies `note_len`

Decode-only alignment rejection:

- `start_time % 60 == 0`
- `distance_m % 10 == 0`
- `end_time > start_time`

`fitlap laps --export --input <fit> --stem <stem> --output <json>` does not use decode-only alignment rejection; it stages laps first and exports from staging.
