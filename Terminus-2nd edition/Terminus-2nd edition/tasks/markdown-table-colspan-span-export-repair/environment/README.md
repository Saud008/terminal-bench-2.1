# mdtable

Export Markdown pipe tables with colspan/rowspan extensions.

```bash
cargo build --release --locked -p mdtable
install -m 0755 target/release/mdtable /usr/local/bin/mdtable
mdtable export --input /app/fixtures/tables/001-basic.md \
  --export /app/output/001-basic.json --format json
```

See `/app/docs/` for contracts.
