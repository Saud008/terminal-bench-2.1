# Fixture catalog

All demos live under `/app/fixtures/demos/`. Seeds are listed in `/app/fixtures/seeds.json`; the default build seed is the first entry (`primary01`).

| Relative path | Purpose |
|---------------|---------|
| `alpha/late.dem` | Baseline ticks in nested `alpha/` tree |
| `beta/early.dem` | Companion nested demo under `beta/` for merge-order coverage |
| `signon/reset.dem` | SIGNON_RESET mid-stream changes tick base |
| `strings/highidx.dem` | String table index 129 (unsigned byte) resolves to label str_129 |
| `loop/session.dem` | `loops_packet_stream` replays usercmds once |
| `broken/trunc.dem` | Truncated final USERCMD body — `probe` must exit 2 |

Full-tree `build` uses every row except `broken/trunc.dem` (listed for `probe` only).
