# Fixture catalog

| Scenario | Stream |
|----------|--------|
| `multi-msg-routing` | `streams/multi-msg-routing.bin` |
| `signed-gps-decode` | `streams/signed-gps-decode.bin` |
| `event-order` | `streams/event-order.bin` |
| `length-edge` | `streams/length-edge.bin` |
| `crc-catalog` | `streams/crc-catalog.bin` |
| `merged-regression` | `streams/merged-regression.bin` |
| `seq-rollback-drop` | `streams/seq-rollback-drop.bin` |
| `dedup-replay` | `streams/dedup-replay.bin` |
| `u8-wrap-forward` | `streams/u8-wrap-forward.bin` |
| `checkpoint-resume-a` | `streams/checkpoint-resume-a.bin` |
| `checkpoint-resume-b` | `streams/checkpoint-resume-b.bin` |
| `checkpoint-resume-c` | `streams/checkpoint-resume-c.bin` |
| `checkpoint-session-a` | `streams/checkpoint-session-a.bin` |
| `checkpoint-resume-session-trap` | `streams/checkpoint-resume-session-trap.bin` |
| `dedup-compid-trap` | `streams/dedup-compid-trap.bin` |
| `mixed-invalid-crc` | `streams/mixed-invalid-crc.bin` |
| `preamble-noise` | `streams/preamble-noise.bin` |

Catalog entries and seeds are listed in `/app/fixtures/catalog.json` and `/app/fixtures/seeds.json`. Seeds permute frame processing order before validation.
