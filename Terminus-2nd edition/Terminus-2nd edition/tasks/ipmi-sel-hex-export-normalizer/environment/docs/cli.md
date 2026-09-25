# sel-chain CLI

Binary: /app/bin/sel-chain

## ingest

```
sel-chain ingest --input <path/to.sel.bin> --db <path/to.db>
```

Creates the database schema if missing, parses the SEL blob per /app/docs/ipmi-sel.md, writes /app/state/sel.stage beside the database parent directory.

## export

```
sel-chain export --db <path/to.db> --out <path/to.csv>
```

Requires a prior ingest on the same database. Emits CSV per /app/docs/export-format.md.
