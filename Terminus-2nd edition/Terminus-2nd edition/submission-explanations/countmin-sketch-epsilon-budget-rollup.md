# Submission explanations — countmin-sketch-epsilon-budget-rollup

**Task folder:** tasks/countmin-sketch-epsilon-budget-rollup/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a multi-stage Count-Min Sketch combiner where approximate sketch math, differential privacy accounting, and deterministic export interact. Hash seed and namespace salt compatibility must be validated before any staging file is written, so partial ingest fixes fail atomic rejection tests. Window overlap weighting uses intersection duration rather than union span, and conservative merge requires per-cell max after scaling—not summing counters across shards. Epsilon lineage must use L2 composition, and export is blocked unless merge_generation matches the persisted generation file. Randomized seeds shift hash seeds and hidden TB3_WIDTH_BIAS fixtures change table width, so hardcoded estimates cannot pass.

## Solution Explanation

The oracle patches ingest validation order, namespace key hashing, overlap intersection math, L2 epsilon composition, conservative max merge, and export generation gating across separate Rust modules. ingest loads bundles, validates shard parameters, computes overlap weights, and writes /app/state/cms-merge-stage.json. merge rebuilds weighted sketch tables from shard updates, applies cell-wise max, and increments /app/state/merge-generation.json. export reads staging and the generation file, emits estimates for bundle query keys, and writes the lineage rollup with a canonical stage digest. cmsctl is rebuilt from the workspace after copying golden module sources.

## Verification Explanation

Pytest drives real cmsctl subprocess commands on bundled and hidden fixture directories with independent reference_sketch.py recomputing Count-Min estimates. Tests cover staging overlap_ms and window_weights, epsilon lineage composition, seed-derived hash offsets, atomic rejection for seed mismatch zero overlap and namespace split traps, generation persistence gates, and TB3_WIDTH_BIAS hidden width shifts. The verifier rebuilds cmsctl in test.sh before pytest. Oracle reward requires all behavioral tests pass with the golden module patches applied.
