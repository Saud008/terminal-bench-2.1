# rigbundle CLI surface

Binary path: /app/bin/rigbundle

## Subcommands

### ingest

```
rigbundle ingest --exif PATH --mount PATH
```

Writes /app/state/capture-staging.json and bumps /app/state/staging-seq.json

### align

```
rigbundle align --lenses PATH --checkerboard PATH
```

Writes /app/state/align-generation.json and /app/output/rejected-captures.jsonl

### export

```
rigbundle export
```

Writes /app/output/bundle-manifest.json; refuses when align_generation is zero

### run

```
rigbundle run --exif PATH --mount PATH --lenses PATH --checkerboard PATH
```

Executes ingest, align, and export in order.

## Environment

TB3_FIXTURE_DIR overrides fixture root for hidden verifier runs.
