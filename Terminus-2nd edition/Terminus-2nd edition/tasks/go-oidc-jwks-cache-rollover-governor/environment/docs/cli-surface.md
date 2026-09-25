# oidcgov CLI surface

Fixed verb order: load-transcript, hydrate-cache, decide-batch, emit-report.

Binary path: /app/bin/oidcgov

## load-transcript

oidcgov load-transcript --scenario SCENARIO [--fixture-dir DIR]

Reads jwks_timeline.jsonl, token_batch.jsonl, policy.json under DIR/scenarios/SCENARIO/.

## hydrate-cache

oidcgov hydrate-cache --scenario SCENARIO

Writes /app/state/jwks-cache-snapshot.json and increments /app/state/hydrate-revision.json counter.

## decide-batch

oidcgov decide-batch --scenario SCENARIO

Writes /app/state/verification-decisions.json file.

## emit-report

oidcgov emit-report --scenario SCENARIO [--output PATH]

Blocked when hydrate_revision is zero. Default output path is /app/output/verification-governance-report.json

internal/wrap is not authoritative for emit-report emit.
