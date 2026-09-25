# par-chain CLI

All paths are absolute under `/app`.

## reconcile

```text
par-chain reconcile --joblog <joblog.tsv> --par-dir <directory>
```

Loads the GNU parallel joblog into `/app/state/manifest.db`, then merges every `*.par` file in `--par-dir` by `seq`. Creates the schema if needed.

## stage

```text
par-chain stage --joblog <joblog.tsv> --par-dir <directory>
```

Requires a prior reconcile. Writes `/app/state/job.manifest.json` per `/app/docs/manifest-format.md`.

## export

```text
par-chain export --joblog <joblog.tsv> --par-dir <directory> --out <report.json>
```

Requires reconcile and stage. Writes the export report per `/app/docs/export-format.md`.
