# Submission explanations — collectd-parse-write-plugin-metric-batch-repair

**Task folder:** tasks/collectd-parse-write-plugin-metric-batch-repair/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-29T14:35:00Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

Agents must repair eight interacting Go packages so PUTVAL ingest, flush bucketing, staging persistence, and JSON export all agree with contracts spread across seven docs files. Partial fixes are trapped by pytest that swaps golden copies of individual modules back to broken originals while keeping the agent’s pipeline.go, so export-only patches that add new cross-package calls fail to compile. Export must publish the staged snapshot after ingest_binding verification rather than re-parsing batch files, which is easy to miss when bundled ingest tests turn green first. The pipeline-api-contract now lists every ingestBatches dependency agents must preserve, but derive-rate pairing, skew edges, and counter-wrap handling still require reading metric-contract.md rather than inferring from fixtures alone.

## Solution Explanation

The oracle copies golden sources into internal/parse, normalize, flush, staging, export, and pipeline, then rebuilds collectdctl. ingestBatches must keep calling parse.ParseStream, normalize.ExpandReadings, normalize.PairRates, flush.WithinSkew, parse.TypeName, flush.FlushIndex, and flush.FlushBounds exactly as in the starter template. pipeline.Export should read staging.Read, call staging.Verify on the envelope, and pass the verified snapshot to export.Write without calling ingestBatches again. Staging.Write must compute ingest_binding from the report payload fields documented in staging-contract.md so export verification and binding tests agree.

## Verification Explanation

Pytest rebuilds the CLI in test.sh and drives collectdctl ingest, stage, and export through subprocess on every run. An independent reference implementation inside test_outputs.py recomputes expected flush JSON from the same fixtures and config seed, so copying bundled outputs cannot pass. Partial-fix tests restore broken module sources, apply one golden patch, and assert exports still mismatch reference results or fail compile when pipeline.go drifts from the locked API surface. Staging and export tests assert snapshot bytes, binding digests, and metric order are preserved without re-ingest during export.
