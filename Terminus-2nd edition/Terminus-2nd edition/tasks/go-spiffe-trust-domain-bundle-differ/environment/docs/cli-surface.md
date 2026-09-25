# spiffectl CLI surface

Fixed verb order: bind-pair, normalize-trust, emit-atlas.

Binary path: /app/bin/spiffectl

## bind-pair

spiffectl bind-pair --scenario SCENARIO [--fixture-dir DIR]

Reads left.json and right.json under DIR/scenarios/SCENARIO/.

## normalize-trust

spiffectl normalize-trust --scenario SCENARIO

Writes /app/state/trust-left-normalized.json, /app/state/trust-right-normalized.json, and increments /app/state/trust-seal-counter.json.

## emit-atlas

spiffectl emit-atlas --scenario SCENARIO [--output PATH]

Blocked when seal_counter is zero. Default output: /app/output/federation-atlas.json.

internal/wrap is not authoritative for emit-atlas emission.
