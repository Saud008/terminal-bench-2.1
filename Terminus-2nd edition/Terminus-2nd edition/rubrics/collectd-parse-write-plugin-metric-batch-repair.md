# Platform rubric — collectd-parse-write-plugin-metric-batch-repair

**Task folder:** tasks/collectd-parse-write-plugin-metric-batch-repair/

Agent rebuilds collectdctl with go build -mod=readonly after editing internal packages, +2
Agent repairs parse.ParseStream and PUTVAL identifier escaping per putval-format.md, +3
Agent implements normalize.ExpandReadings and PairRates for derive and counter kinds, +3
Agent assigns flush windows with FlushIndex and FlushBounds aligned to metric-contract.md, +3
Agent enforces flush.WithinSkew rejection using the configured time skew buffer, +2
Agent persists staging snapshot with correct ingest_binding on collectdctl stage, +3
Agent verifies ingest_binding on export before calling export.Write with staged envelope, +3
Agent keeps pipeline.go ingestBatches call sites stable per pipeline-api-contract.md, +2
Agent removes export-time re-ingest so export publishes staged report verbatim, +3
Agent fixes export JSON field order without reordering staged flush or metric rows, +2
Agent patches export alone while pipeline.Export still re-reads batch files, -3
Agent renames export.Write or changes its envelope parameter list, -3
Agent adds new cross-package helpers in pipeline.go beyond the starter template, -3
Agent fixes putval parsing alone while derive rate pairing still fails bundled batches, -2
Agent fixes staging binding alone while export still re-ingests from fixtures, -2
