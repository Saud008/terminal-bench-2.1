# fitlap CLI reference

Binary: `/usr/local/bin/fitlap`

## decode

```bash
fitlap decode <fit-file>
```

- Validates CRC before lap parsing.
- Enforces decode-only alignment rejection.
- Emits a JSON summary to stdout.

## laps export

```bash
fitlap laps --export --input <fit> --stem <stem> --output <json>
```

- Writes staging file to `/app/state/lap-staging/<stem>.json`
- Writes export file to `--output`
- Export uses staging rows and does not re-parse FIT for already staged laps.
