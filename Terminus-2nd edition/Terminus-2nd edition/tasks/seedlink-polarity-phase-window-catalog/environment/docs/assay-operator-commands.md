# Assay operator commands — seedcat

Operator surface for the seismic phase-window calibration laboratory workflow. See `/app/docs/scientific-computing-workflow.md` for numerical closure scope.

Invocable as `seedcat` (installed at `/usr/local/bin/seedcat`).

## decode

```bash
seedcat decode <slws-file>
```

- Validates CRC before pick chronology parse.
- Enforces decode-only pick invariant rejection (unique sample indices within sample_count).
- Emits a JSON summary to stdout.

## ingest

```bash
seedcat ingest --input <slws> --stem <stem>
```

- Parses SLWS and writes staging JSON to `/app/state/phase-staging/<stem>.json` only.

## catalog export

```bash
seedcat catalog --export --input <slws> --stem <stem> --output <json>
```

- Writes staging file to `/app/state/phase-staging/<stem>.json`
- Writes export catalog to `--output`
- Export reads staging rows and does not re-parse SLWS when staging already exists.
