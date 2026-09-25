# CLI

Binary: /app/bin/icc-drift-bundler

| Subcommand | Required flags | Optional flags |
|------------|----------------|----------------|
| ingest | --readings PATH, --profile PATH, --paper PATH | |
| evaluate | --readings PATH, --profile PATH, --paper PATH, --policy PATH, --tickets PATH, --as-of EPOCH | |
| export | --readings PATH, --out PATH | |
| run | --readings, --profile, --paper, --policy, --tickets, --as-of, --out | |

Staging default path: dirname(readings)/icc.stage.json

Export default output: /app/output/drift-report.json

export exits 2 when summary.drift_count is greater than zero, otherwise 0.
