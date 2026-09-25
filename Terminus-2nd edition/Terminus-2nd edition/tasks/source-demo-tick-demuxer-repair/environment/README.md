# demo-index

`demo-index` rebuilds a merged tick timeline from nested SRCDEM (`.dem`) files.

- Contract: `/app/docs/demo-format.md`, `/app/docs/index-schema.md`, `/app/docs/exit-codes.md`
- Fixtures: `/app/docs/fixture-catalog.md`
- Implementation: `/app/lib/`, `/app/bin/demo-index`, `/app/bin/demux-read`

```bash
/app/bin/demo-index build --root /app/fixtures/demos --seed primary01 --out /app/output/tick-index.json
/app/bin/demo-index probe --demo /app/fixtures/demos/broken/trunc.dem
```
