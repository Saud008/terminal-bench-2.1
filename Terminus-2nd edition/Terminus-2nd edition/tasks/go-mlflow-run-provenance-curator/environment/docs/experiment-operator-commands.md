# Experiment operator commands

mlprov is installed at /usr/local/bin/mlprov. Rebuild kernels from /app when sources change (see /app/docs/build-toolchain.md).

## hydrate

```
mlprov ingest --seed <seed> --scenario <name>
```

Writes the feature-run snapshot to `/app/state/provenance-staging.json`.

## bind closure

```
mlprov curate bind --seed <seed> --scenario <name>
```

Persists the latest active closure row for the seed in `/app/work/provenance.db`.

## publish certificate

```
mlprov export summary --seed <seed> --scenario <name> --output <path>
```

Writes eval summary certificate JSON to the caller-provided path under `/app/output/`.
