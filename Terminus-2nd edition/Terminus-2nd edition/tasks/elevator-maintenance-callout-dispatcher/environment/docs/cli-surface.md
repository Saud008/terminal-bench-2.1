# calloutd CLI surface

Binary path: /app/bin/calloutd.

## load-roster

Materialize a scenario bundle into /app/state/callout.db.

Flags: --scenario NAME, --fixture-dir PATH (default /app/fixtures).

## rank-faults

Compute ranked urgency_scores and write /app/work/urgency-snapshot.json.

Flags: --scenario NAME.

## bind-roster

Greedy technician binding with stable tie-break precedence. Increments callout_pass.

Flags: --scenario NAME.

## emit-callout

Publish /app/output/callout-roster.json when callout_pass is positive.

Flags: --scenario NAME, --output PATH optional.
