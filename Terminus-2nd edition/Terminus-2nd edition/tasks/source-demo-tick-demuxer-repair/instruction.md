The demo-index tool at /app/bin/demo-index walks nested SRCDEM demo files under /app/fixtures/demos/ and must emit a merged tick timeline. Extend the shell pipeline under /app/lib/ so build and probe outputs match /app/docs/demo-format.md, /app/docs/index-schema.md, and /app/docs/exit-codes.md for every catalog fixture in /app/docs/fixture-catalog.md except broken/trunc.dem, which is probe-only. Reasoning must follow canonical relative-path ordering, unsigned string-index semantics, signon tick-base resets, and loop replay dedupe rules from those contracts.

Run /app/bin/demo-index build with --root /app/fixtures/demos, --seed from /app/fixtures/seeds.json, and --out /app/output/tick-index.json. Run /app/bin/demo-index probe with --demo /app/fixtures/demos/broken/trunc.dem. Builds must work with the default seed primary01 and with alternate seeds alt_gamma and alt_delta, which change masked arg values per file.

Export JSON must follow /app/docs/index-schema.md. Binary layout is in /app/docs/demo-format.md.

Do not edit /app/docs/, /app/fixtures/, /app/tools/gendemo.py, or /app/src/demux.c.
