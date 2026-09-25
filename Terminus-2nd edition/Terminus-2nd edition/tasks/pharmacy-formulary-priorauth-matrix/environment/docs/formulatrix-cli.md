# formulatrix CLI surface

Fixed verb order: load-scenario, refresh-db, publish-matrix.

Binary path: /app/bin/formulatrix

## load-scenario

formulatrix load-scenario --scenario SCENARIO [--fixture-dir DIR] [--as-of DATE]

Reads scenarios/SCENARIO/scenario.json from the fixture root.

## refresh-db

formulatrix refresh-db --scenario SCENARIO

Writes /app/state/formulary.db and increments /app/state/refresh-revision.json.

## publish-matrix

formulatrix publish-matrix --scenario SCENARIO [--output PATH]

Blocked when refresh_revision is zero. Default output: /app/output/formulary-matrix.json.

internal/decoy/lexicon is not authoritative for publish-matrix.
