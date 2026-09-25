# Submission explanations — airspace-notam-sector-impact-weaver

**Task folder:** tasks/airspace-notam-sector-impact-weaver/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Five aviation rules interact before any sealed report is valid. Amendment series keep only the highest amendment, midnight windows wrap the day, ray cast polygons and runway normalization disagree with naive checks, and airway expansion joins duplicate fixes. Weave revision must be positive before emit seals digests, so one module fix still leaves other scenarios wrong.

## Solution Explanation

The approach implements the four CLI verbs on the working Go tree and rebuilds notamweave offline. Correct amendment suppression, midnight windows, runway stripping, ray cast containment, and airway join dedupe feed weave revision bumps and a sorted report seal. Bundle digests include policy and fix points so Python reference math matches Go encoding.

## Verification Explanation

Pytest rebuilds the binary and drives notamweave via subprocess on bundled and hidden fixture probes. Independent reference math recomputes digests, active counts, and route impacts. Separate checks require the active cache and impact ledger, block emit without weave revision, and assert midnight and amendment traps.
