# iceexpctl CLI surface

Fixed verb order: capture-catalog, audit-retention, publish-expiry.

Binary path: /app/bin/iceexpctl

## capture-catalog

iceexpctl capture-catalog --catalog NAME --scenario SCENARIO [--fixture-dir DIR]

Reads tables/SCENARIO/table.json and manifests under tables/SCENARIO/manifests/ in numeric meta order. The catalog name must match table_name in metadata.

## audit-retention

iceexpctl audit-retention --catalog NAME --scenario SCENARIO

Writes /app/work/analyze-findings.json and increments /app/state/analyze-revision.json.

## publish-expiry

iceexpctl publish-expiry --catalog NAME --scenario SCENARIO [--plan-out PATH] [--orphan-out PATH]

Blocked when analyze_revision is zero. Default outputs: /app/output/expiry-plan.json and /app/output/orphan-ledger.jsonl.

internal/decoy/metaparse is not authoritative for publish-expiry planemit.
