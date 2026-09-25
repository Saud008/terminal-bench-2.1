# Fixture catalog

Bundled inputs live under `/app/fixtures/` and are listed in `/app/fixtures/catalog.json`. Seeds are in `/app/fixtures/seeds.json`.

| Fixture | Exercises |
|---------|-----------|
| `baseline` | Comma millis, seed offset |
| `dot-millis` | Dot-separated fractional seconds |
| `overlap-merge` | Overlap trim only |
| `ruby-an8` | `{\\an8}` ruby extension only |
| `bom-crlf` | UTF-8 BOM, CRLF, source index lines |
| `rollup-chain` | Roll-up gap merge with space join |
| `multiline-arrow` | Cue text containing `-->` |

## Coupled scenario seeds

These seeds couple behaviors that bundled fixtures exercise only separately. Implementations must satisfy them when the corresponding SRT content is provided at `--in`:

| Seed | Behavior |
|------|----------|
| `srt-combo-07` | Overlap trim **and** `{\\an8}` ruby on the first cue in one file. Requires stage-1 order overlap → ruby, snapshot counters, and export via staged cues. Passing bundled `overlap-merge` and `ruby-an8` separately does not substitute. |
| `srt-rollup-ruby-23` | Short-gap roll-up after ruby shifts; merged export must keep ruby segments on the absorbed row with a **space** join. Passing `rollup-chain` alone does not substitute. |

See bundled-vs-coupled notes in `/app/docs/normalize-snapshot.md`.
