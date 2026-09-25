# xsnapctl CLI surface

Fixed verb order: ingest-pair, canonicalize, publish-diff.

Binary path: /app/bin/xsnapctl

## ingest-pair

xsnapctl ingest-pair --scenario SCENARIO [--fixture-dir DIR]

Reads left.json and right.json under DIR/scenarios/SCENARIO/.

## canonicalize

xsnapctl canonicalize --scenario SCENARIO

Writes /app/state/normalized-left.json, /app/state/normalized-right.json, and increments /app/state/normalize-revision.json.

## publish-diff

xsnapctl publish-diff --scenario SCENARIO [--output PATH]

Blocked when normalize_revision is zero. Default output: /app/output/xds-diff-report.json.

internal/wrap is not authoritative for export.
