# filingatlas CLI surface

Fixed verb order: load-bundle, index-parties, scan-risks, emit-atlas.

Binary path: /app/bin/filingatlas

## load-bundle

filingatlas load-bundle --scenario SCENARIO [--fixture-dir DIR]

Reads dockets.jsonl, parties.json, pages.jsonl, sealed_terms.json, policy.json under DIR/scenarios/SCENARIO/.

## index-parties

filingatlas index-parties --scenario SCENARIO

Writes /app/state/party-graph.json and increments /app/state/index-revision.json.

## scan-risks

filingatlas scan-risks --scenario SCENARIO

Writes /app/state/risk-findings.json.

## emit-atlas

filingatlas emit-atlas --scenario SCENARIO [--output PATH]

Blocked when index_revision is zero. Default output: /app/output/redaction-risk-atlas.json.

internal/telemetry is not authoritative for emit-atlas emission.
