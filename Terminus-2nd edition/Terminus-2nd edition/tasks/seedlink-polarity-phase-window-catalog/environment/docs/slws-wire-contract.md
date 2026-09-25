# SLWS snippet wire contract

Waveform assay wire layout for seismic calibration closure. Reference math scope: `/app/docs/scientific-computing-workflow.md`.

SLWS is a little-endian binary container for SeedLink-style waveform snippets used by seedcat.

## Header layout

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Magic ASCII SLWS |
| 4 | 1 | Version (must be 1) |
| 5 | 2 | Network code (2 ASCII bytes) |
| 7 | 4 | Station id (4 ASCII bytes, NUL padded) |
| 11 | 4 | epoch_sec u32 LE — UTC epoch at sample 0 |
| 15 | 1 | leap_marker u8 — 1 when recording spans a positive leap second |
| 16 | 2 | sample_count u16 LE |
| 18 | 4 | rate_mhz u32 LE — sample rate in millihertz (100000 = 100 Hz) |
| 22 | 1 | body_polarity i8 — hint only; polarity sheets override |
| 23 | 2 | mask_len u16 LE |
| 25 | mask_len | clip_mask bytes — LSB-first bit mask (bit 0 = sample 0) |
| 25+mask_len | 1 | pick_count u8 |
| picks | pick_count * 3 | u16 sample_idx LE, u8 phase_code |
| samples | sample_count * 2 | i16 LE sample amplitudes |
| end | 2 | crc16 u16 LE — sum of all preceding bytes mod 65536 |

## Phase codes

| Code | Phase |
|------|-------|
| 0 | P |
| 1 | S |
| 2 | X (other) |

## Decode-only invariant

decode rejects snippets when any pick sample_idx is out of range or duplicated. catalog export does not apply this rejection.

## CRC

crc16 is the low 16 bits of the unsigned sum of every byte before the checksum field.
