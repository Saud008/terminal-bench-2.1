# Submission explanations - ais-voyage-leg-anomaly-segmenter

**Task folder:** tasks/ais-voyage-leg-anomaly-segmenter/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T18:00:00Z

**Category note:** Zip metadata uses `data-processing` (AIS stream normalize + voyage-leg atlas). Choose **data-processing** on the platform form.

> Agent scaffold only - rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Hard because feed and atlas split MMSI collapse, burst windows, ray-cast ports, impossible-speed gates, and none-labeled leg splits across modules while fixtures put higher seq first so first-seen dedupe fails. Numeric ordinal atlas order plus TB3_AIS_DIR overlays block partial patches that only pass the happy-path bundle.

## Solution Explanation

The oracle installs corrected codec, MMSI lowest-seq dedupe without station, burst-enabled feed, ray-cast ports, sog gate, and stable atlas emit, then rebuilds aissegment. Keep lowest seq on MMSI and burst ties, sort voyage_legs by mmsi then numeric L{n} ordinal, and emit leg_chain_digest over that order.

## Verification Explanation

The verifier rebuilds aissegment then runs pytest against an independent reference from fixed-hash fixtures. Bundled and hidden streams cover port entry with none, MMSI lowest-seq, speed suppression, draught splits, burst lowest-seq, and edge-port jitter via TB3_AIS_DIR. NOP scores zero; oracle scores one.
